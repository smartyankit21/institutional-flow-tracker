import time
import requests
import pandas as pd

class MultiExchangeFetcher:
    NSE_BASE = "https://www.nseindia.com"
    BSE_BASE = "https://api.bseindia.com/BseIndiaAPI/api"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self._init_nse()

    def _init_nse(self):
        try:
            self.session.get(self.NSE_BASE, timeout=10)
            time.sleep(1)
        except Exception:
            pass

    def fetch_nse_deals(self) -> pd.DataFrame:
        url = f"{self.NSE_BASE}/api/snapshot-capital-market-largedeal"
        try:
            res = self.session.get(url, timeout=10)
            if res.status_code != 200:
                self._init_nse()
                res = self.session.get(url, timeout=10)
            data = res.json()
            df = pd.concat([
                pd.DataFrame(data.get("BULK_DEALS_DATA", [])),
                pd.DataFrame(data.get("BLOCK_DEALS_DATA", []))
            ], ignore_index=True)
            if df.empty:
                return pd.DataFrame()
            df = df.rename(columns={"date": "Date", "symbol": "Symbol", "clientName": "Client_Name", "buySell": "Side", "qty": "Quantity", "price": "Price"})
            df["Exchange"] = "NSE"
            return self._clean(df)
        except Exception as e:
            print(f"[NSE Deals Error] {e}")
            return pd.DataFrame()

    def fetch_bse_deals(self) -> pd.DataFrame:
        url = f"{self.BSE_BASE}/BulkDeals/w"
        try:
            res = self.session.get(url, headers={"Referer": "https://www.bseindia.com/"}, timeout=10)
            if res.status_code != 200:
                return pd.DataFrame()
            df = pd.DataFrame(res.json().get("Table", []))
            if df.empty:
                return pd.DataFrame()
            df = df.rename(columns={"Deal_Date": "Date", "scrip_cd": "Symbol", "client_name": "Client_Name", "DealType": "Side", "qty": "Quantity", "price": "Price"})
            df["Exchange"] = "BSE"
            df["Side"] = df["Side"].replace({"B": "BUY", "S": "SELL"})
            return self._clean(df)
        except Exception as e:
            print(f"[BSE Deals Error] {e}")
            return pd.DataFrame()

    def fetch_sast_pledges(self) -> pd.DataFrame:
        url = f"{self.NSE_BASE}/api/corporates-sast-reg31?index=equities"
        try:
            res = self.session.get(url, timeout=10)
            if res.status_code == 200:
                return pd.DataFrame(res.json().get("data", []))
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df["Quantity"] = pd.to_numeric(df["Quantity"].astype(str).str.replace(",", ""), errors="coerce")
        df["Price"] = pd.to_numeric(df["Price"].astype(str).str.replace(",", ""), errors="coerce")
        df["Value_Cr"] = (df["Quantity"] * df["Price"]) / 1e7
        df["Side"] = df["Side"].str.upper().str.strip()
        df["Client_Name"] = df["Client_Name"].str.strip().str.upper()
        return df.dropna(subset=["Quantity", "Price", "Value_Cr"])
