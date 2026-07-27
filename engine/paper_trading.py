import json
import os
from datetime import datetime

PORTFOLIO_FILE = "data/portfolio.json"

DEFAULT_PORTFOLIO = {
    "intraday_capital": 100000.0,
    "swing_capital": 100000.0,
    "cash": 200000.0,
    "intraday_positions": [],
    "swing_positions": [],
    "positions": [],
    "history": [],
    "last_updated": ""
}

def load_portfolio():
    """Loads portfolio state from disk and injects missing default keys."""
    if not os.path.exists(PORTFOLIO_FILE):
        save_portfolio(DEFAULT_PORTFOLIO)
        return DEFAULT_PORTFOLIO.copy()
    
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            data = json.load(f)
        for key, val in DEFAULT_PORTFOLIO.items():
            if key not in data:
                data[key] = val
        return data
    except Exception as e:
        print(f"⚠️ Portfolio load note: {e}. Re-initializing state.")
        save_portfolio(DEFAULT_PORTFOLIO)
        return DEFAULT_PORTFOLIO.copy()

def save_portfolio(data):
    """Saves portfolio state to data/portfolio.json."""
    os.makedirs("data", exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(data, f, indent=2)

def execute_paper_trades(predictions, mode):
    """
    Executes paper trades safely across dynamic intraday and swing search predictions.
    """
    portfolio = load_portfolio()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trades_executed = []

    if mode in ["morning", "intraday_search"]:
        intraday_preds = predictions[:5]
        alloc = portfolio.get("intraday_capital", 100000.0) / max(len(intraday_preds), 1)
        
        for p in intraday_preds:
            price = p.get("price", 100.0)
            trade = {
                "timestamp": timestamp,
                "mode": mode,
                "type": "INTRADAY",
                "symbol": p.get("symbol"),
                "action": p.get("signal"),
                "price": price,
                "quantity": max(1, int(alloc / max(price, 1))),
                "status": "OPEN"
            }
            trades_executed.append(trade)
            portfolio["intraday_positions"].append(trade)
            portfolio["history"].append(trade)

    elif mode in ["evening", "swing_search"]:
        swing_preds = predictions[:10]
        alloc = portfolio.get("swing_capital", 100000.0) / max(len(swing_preds), 1)

        for p in swing_preds:
            price = p.get("price", 100.0)
            trade = {
                "timestamp": timestamp,
                "mode": mode,
                "type": "SWING",
                "symbol": p.get("symbol"),
                "action": p.get("signal"),
                "price": price,
                "quantity": max(1, int(alloc / max(price, 1))),
                "status": "HOLDING"
            }
            trades_executed.append(trade)
            portfolio["swing_positions"].append(trade)
            portfolio["history"].append(trade)

    save_portfolio(portfolio)
    return trades_executed
