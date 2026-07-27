import os
import requests
import pandas as pd
import yfinance as yf

def get_market_universe():
    """
    Dynamically fetches the live NIFTY 500 stock universe from web sources 
    at runtime. Zero hardcoded stock lists.
    """
    tickers = []
    
    # Primary Source: Scrape live NIFTY 500 index table online
    try:
        url = "https://en.wikipedia.org/wiki/NIFTY_500"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        tables = pd.read_html(response.text)
        
        for table in tables:
            if 'Symbol' in table.columns:
                symbols = table['Symbol'].dropna().tolist()
                tickers = [f"{str(s).strip()}.NS" for s in symbols if str(s).strip()]
                print(f"🌐 Dynamically fetched {len(tickers)} stocks from live NIFTY 500 web feed.")
                break
    except Exception as e:
        print(f"⚠️ Live web scrape note: {e}. Trying secondary live index feed...")

    # Secondary Source: Direct public index dataset mirror
    if not tickers:
        try:
            csv_url = "https://raw.githubusercontent.com/anandmurali88/nifty500-list/main/nifty500.csv"
            df = pd.read_csv(csv_url)
            if 'Symbol' in df.columns:
                tickers = [f"{str(s).strip()}.NS" for s in df['Symbol'].dropna() if str(s).strip()]
                print(f"🌐 Dynamically fetched {len(tickers)} tickers from secondary live feed.")
        except Exception as e:
            print(f"⚠️ Secondary feed note: {e}")

    unique_tickers = list(dict.fromkeys(tickers))
    return unique_tickers if unique_tickers else []

def fetch_stock_data(symbol, period="5d", interval="15m"):
    """
    Fetches live market candles using yfinance.
    Safely falls back to daily close candles during off-market hours or weekends
    so the AI engine never crashes when analyzing market structure off-hours.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        # Off-market / weekend guard: Fall back to daily candles if intraday is empty
        if df is None or df.empty:
            df = ticker.history(period="1mo", interval="1d")

        if df is None or df.empty:
            return None

        df = df.dropna(subset=['Close'])
        df.reset_index(inplace=True)
        if 'Datetime' in df.columns:
            df.rename(columns={'Datetime': 'Date'}, inplace=True)
        
        return df

    except Exception:
        return None
