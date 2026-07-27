import json
import os
from datetime import datetime

class PaperTradingEngine:
    def __init__(self, filepath="data/paper_trading.json"):
        self.filepath = filepath
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                return json.load(f)
        return {
            "intraday_capital": 200000.0,
            "swing_capital": 200000.0,
            "active_intraday_positions": [],
            "active_swing_positions": [],
            "completed_trades": []
        }

    def save(self):
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=2)

    def execute_morning_allocation(self, top_intraday, top_swing):
        today = datetime.now().strftime("%Y-%m-%d")
        
        intra_alloc = self.data["intraday_capital"] / max(1, len(top_intraday))
        self.data["active_intraday_positions"] = []
        for stock in top_intraday:
            qty = int(intra_alloc // stock["entry_price"])
            if qty > 0:
                self.data["active_intraday_positions"].append({
                    "date": today,
                    "symbol": stock["symbol"],
                    "qty": qty,
                    "entry_price": stock["entry_price"],
                    "target": stock["target_price"],
                    "stop_loss": stock["stop_loss"],
                    "allocated_capital": round(qty * stock["entry_price"], 2),
                    "status": "OPEN"
                })

        swing_alloc = self.data["swing_capital"] / max(1, len(top_swing))
        self.data["active_swing_positions"] = []
        for stock in top_swing:
            qty = int(swing_alloc // stock["entry_price"])
            if qty > 0:
                self.data["active_swing_positions"].append({
                    "date": today,
                    "symbol": stock["symbol"],
                    "qty": qty,
                    "entry_price": stock["entry_price"],
                    "target": stock["target_price"],
                    "stop_loss": stock["stop_loss"],
                    "allocated_capital": round(qty * stock["entry_price"], 2),
                    "status": "OPEN"
                })

        self.save()

    def settle_intraday_market_close(self, current_market_data):
        total_pnl = 0.0
        for pos in self.data["active_intraday_positions"]:
            sym = pos["symbol"]
            curr_price = current_market_data.get(sym, {}).get("current_price", pos["entry_price"])
            
            pnl = (curr_price - pos["entry_price"]) * pos["qty"]
            pos["exit_price"] = curr_price
            pos["pnl"] = round(pnl, 2)
            pos["status"] = "CLOSED"
            
            total_pnl += pnl
            self.data["completed_trades"].append(pos)

        self.data["intraday_capital"] = round(self.data["intraday_capital"] + total_pnl, 2)
        self.data["active_intraday_positions"] = []
        self.save()
        return total_pnl
