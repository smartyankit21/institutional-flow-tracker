import pandas as pd
from src.classifier import classify_client, match_hni

def analyze_weekly_flows(df_deals: pd.DataFrame) -> tuple[pd.DataFrame, list[dict], list[dict]]:
    if df_deals.empty:
        return pd.DataFrame(), [], []

    df = df_deals.copy()
    df["Category"] = df["Client_Name"].apply(classify_client)
    df["HNI_Name"] = df["Client_Name"].apply(match_hni)

    # 1. Extract Super Investor Trades
    hni_deals = []
    for _, row in df[df["Category"] == "SUPER_INVESTOR"].iterrows():
        val = round(row["Value_Cr"], 2)
        hni_deals.append({
            "Investor": row["HNI_Name"],
            "Symbol": row["Symbol"],
            "Exchange": row["Exchange"],
            "Action": "Accumulate" if row["Side"] == "BUY" else "Reduce",
            "Side": row["Side"],
            "Value_Cr": val,
            "Shares": int(row["Quantity"]),
            "Price": float(row["Price"]),
            "Entity": row["Client_Name"],
            "Priority": "Urgent" if val >= 20 else ("High" if val >= 5 else "Medium")
        })

    # 2. Institutional Supply-Absorption Analysis (Filter HFT Desks)
    clean_inst = df[df["Category"] != "ARBITRAGE"]
    action_table = []
    deep_dives = []

    for symbol, grp in clean_inst.groupby("Symbol"):
        buys = grp[grp["Side"] == "BUY"]
        sells = grp[grp["Side"] == "SELL"]

        buy_cr = round(buys["Value_Cr"].sum(), 2)
        sell_cr = round(sells["Value_Cr"].sum(), 2)

        inst_buys = buys[buys["Category"].isin(["DII", "FII"])]
        inst_buy_cr = round(inst_buys["Value_Cr"].sum(), 2)
        pe_sells = sells[sells["Category"].isin(["PE_VC", "OTHER"])]
        pe_sell_cr = round(pe_sells["Value_Cr"].sum(), 2)

        # Clean Institutional Accumulation
        if buy_cr >= 200 and sell_cr == 0:
            top_buyers = " + ".join(buys["Client_Name"].unique()[:2])
            action_table.append({
                "Symbol": symbol,
                "Category": "Institutional",
                "Action": "Accumulate",
                "Reason": f"Clean ₹{buy_cr:.0f} Cr entry ({top_buyers}); zero institutional supply.",
                "Priority": "Urgent" if buy_cr >= 500 else "High"
            })
            deep_dives.append({
                "Symbol": symbol,
                "Type": "CLEAN_INFLOW",
                "Buy_Val": buy_cr,
                "Participants": buys[["Client_Name", "Category", "Value_Cr"]].to_dict("records")
            })

        # Supply Absorption Diagnostics
        elif pe_sell_cr >= 250 and inst_buy_cr > 0:
            abs_rate = round((inst_buy_cr / pe_sell_cr) * 100, 1)
            unabs = round(pe_sell_cr - inst_buy_cr, 2)
            act = "Near-Accumulate" if abs_rate >= 70 else "Watch"
            action_table.append({
                "Symbol": symbol,
                "Category": "PE Absorption",
                "Action": act,
                "Reason": f"{abs_rate}% absorbed of ₹{pe_sell_cr:.0f} Cr supply. Overhang: ₹{unabs:.0f} Cr.",
                "Priority": "High" if abs_rate >= 70 else "Medium"
            })
            deep_dives.append({
                "Symbol": symbol,
                "Type": "ABSORPTION",
                "Sell_Val": pe_sell_cr,
                "Buy_Val": inst_buy_cr,
                "Absorption": abs_rate,
                "Unabsorbed": unabs,
                "Buyers": inst_buys[["Client_Name", "Category", "Value_Cr"]].to_dict("records")
            })

        # Coordinated Institutional Exit
        elif sell_cr >= 250 and inst_buy_cr == 0:
            action_table.append({
                "Symbol": symbol,
                "Category": "Institutional",
                "Action": "Avoid",
                "Reason": f"₹{sell_cr:.0f} Cr institutional exit with 0% institutional absorption.",
                "Priority": "Urgent"
            })

    return pd.DataFrame(action_table), deep_dives, hni_deals

def process_pledges(df_pledges: pd.DataFrame) -> list[dict]:
    if df_pledges.empty:
        return []
    signals = []
    for symbol, grp in df_pledges.groupby("symbol"):
        created = grp[grp["typeOfEvent"].astype(str).str.upper() == "CREATION"]["sharesTraded"].sum()
        released = grp[grp["typeOfEvent"].astype(str).str.upper() == "INVOCATION"]["sharesTraded"].sum()
        if created > 0 and released > 0:
            signals.append({
                "Symbol": symbol,
                "Category": "Promoter SAST",
                "Action": "Avoid",
                "Reason": f"Rolling pledge cycle (Pledged {created:,.0f} shs, Released {released:,.0f} shs). Operational debt stress.",
                "Priority": "Medium"
            })
        elif created > 0 and released == 0:
            signals.append({
                "Symbol": symbol,
                "Category": "Promoter SAST",
                "Action": "Hold Entry",
                "Reason": f"Fresh pledge of {created:,.0f} shs created with zero release.",
                "Priority": "High"
            })
    return signals
