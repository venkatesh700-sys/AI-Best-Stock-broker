import os
import requests
import pandas as pd
import yfinance as yf

class DynamicMarketFetcher:
    @staticmethod
    def get_nifty_symbols(index_type="nifty50"):
        url_map = {
            "nifty50": "https://en.wikipedia.org/wiki/NIFTY_50",
            "nifty200": "https://en.wikipedia.org/wiki/NIFTY_500"
        }
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            url = url_map.get(index_type, url_map["nifty50"])
            response = requests.get(url, headers=headers, timeout=10)
            tables = pd.read_html(response.text)
            for df in tables:
                col_name = next((col for col in df.columns if "Symbol" in str(col) or "Ticker" in str(col)), None)
                if col_name:
                    symbols = df[col_name].dropna().tolist()
                    clean_symbols = [f"{str(s).strip().upper()}.NS" for s in symbols if isinstance(s, str) and str(s).strip()]
                    return clean_symbols[:100]
        except Exception as e:
            print(f"[Fetcher Warning] Dynamic scraping fallback triggered: {e}")
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", 
                "BHARTIARTL.NS", "SBIN.NS", "LTIM.NS", "TATAMOTORS.NS", "AXISBANK.NS"]

    @staticmethod
    def fetch_live_market_data(symbols):
        data = {}
        for sym in symbols:
            try:
                ticker = yf.Ticker(sym)
                hist = ticker.history(period="5d", interval="15m")
                info = ticker.fast_info
                if not hist.empty:
                    data[sym] = {
                        "current_price": round(info.last_price or hist['Close'].iloc[-1], 2),
                        "prev_close": round(info.previous_close or hist['Close'].iloc[-2], 2),
                        "volume": int(hist['Volume'].iloc[-1]),
                        "avg_volume": int(hist['Volume'].mean()),
                        "high": round(hist['High'].max(), 2),
                        "low": round(hist['Low'].min(), 2)
                    }
            except Exception:
                continue
        return data
