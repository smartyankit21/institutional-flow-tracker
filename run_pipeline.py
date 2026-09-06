import datetime
import pandas as pd
from src.fetcher import MultiExchangeFetcher
from src.engine import analyze_weekly_flows, process_pledges
from src.pdf_styler import export_to_pdf

def run():
    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=7)).strftime("%d %b %Y")
    end_date = today.strftime("%d %b %Y")

    print(f"[Pipeline Initiated] Aggregating week {start_date} – {end_date}...")
    fetcher = MultiExchangeFetcher()
    deals = pd.concat([fetcher.fetch_nse_deals(), fetcher.fetch_bse_deals()], ignore_index=True)
    pledges = fetcher.fetch_sast_pledges()

    actions, deep_dives, hni_deals = analyze_weekly_flows(deals)
    pledge_signals = process_pledges(pledges)

    # Compile Markdown Document
    md = [
        "# Institutional & Super Investor Flow Analysis — Weekly Intelligence",
        f"**Date:** {end_date} Upload  ",
        f"**Period:** {start_date} – {end_date} | Multi-Exchange Engine (NSE & BSE)  \n",
        "---",
        "### Section 1: Master Action Table — This Week\n",
        "| # | Stock | Category | Action | Key Driver & Flow Mechanics | Priority |",
        "| :- | :--- | :--- | :--- | :--- | :--- |"
    ]

    idx = 1
    for _, row in actions.iterrows():
        md.append(f"| {idx} | **{row['Symbol']}** | {row['Category']} | **{row['Action']}** | {row['Reason']} | {row['Priority']} |")
        idx += 1
    for p in pledge_signals:
        md.append(f"| {idx} | **{p['Symbol']}** | {p['Category']} | **{p['Action']}** | {p['Reason']} | {p['Priority']} |")
        idx += 1

    md.extend(["\n---", "### Section 2: Marquee Super Investor & HNI Tracker (33 Monitored Names)\n"])
    if hni_deals:
        md.append("| Investor | Stock | Exchange | Action | Value (₹ Cr) | Qty @ Price | Executing Entity | Priority |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for d in hni_deals:
            md.append(f"| **{d['Investor']}** | **{d['Symbol']}** | {d['Exchange']} | **{d['Side']}** | ₹{d['Value_Cr']} Cr | {d['Shares']:,} @ ₹{d['Price']} | `{d['Entity']}` | {d['Priority']} |")
    else:
        md.append("*No open-market bulk/block deals (≥0.5%) triggered by the 33 marquee investors this week.*")

    md.extend(["\n---", "### Section 3: Institutional Supply-Absorption Deep Dives\n"])
    for dd in deep_dives:
        if dd["Type"] == "CLEAN_INFLOW":
            md.append(f"**{dd['Symbol']} (Clean Inflow)**  \n* **Total Net Buy:** ₹{dd['Buy_Val']} Cr | Zero institutional supply.  \n* **Buyers:**")
            for b in dd["Participants"]:
                md.append(f"  * {b['Client_Name']} ({b['Category']}): ₹{b['Value_Cr']:.1f} Cr")
            md.append("")
        elif dd["Type"] == "ABSORPTION":
            md.append(f"**{dd['Symbol']} (Absorption: {dd['Absorption']}%)**  \n* **Gross Divestment:** ₹{dd['Sell_Val']} Cr | **Absorbed:** ₹{dd['Buy_Val']} Cr | **Float Overhang:** ₹{dd['Unabsorbed']} Cr  \n* **Participating Institutions:**")
            for b in dd["Buyers"]:
                md.append(f"  * {b['Client_Name']} ({b['Category']}): ₹{b['Value_Cr']:.1f} Cr")
            md.append("")

    full_report = "\n".join(md)
    filename_base = f"Weekly_Flow_Report_{today.strftime('%Y_%m_%d')}"

    # Export Markdown
    with open(f"{filename_base}.md", "w", encoding="utf-8") as f:
        f.write(full_report)

    # Export Styled PDF
    export_to_pdf(full_report, f"{filename_base}.pdf")

if __name__ == "__main__":
    run()
