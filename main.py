import argparse
import json
import os

from engine.fetch_data import DynamicMarketFetcher
from engine.agent_swarm import AgentSwarmCore
from engine.paper_trading import PaperTradingEngine
from engine.retrospective import RetrospectiveEngine
from engine.telegram_notifier import TelegramAlertEngine

def main():
    parser = argparse.ArgumentParser(description="AI Stock Trader Main Engine")
    parser.add_argument("--mode", type=str, default="morning", 
                        choices=["morning", "evening", "intraday_search", "swing_search"])
    args = parser.parse_args()

    weights = {"tech_weight": 1.0, "vol_weight": 1.0}
    if os.path.exists("data/weights.json"):
        with open("data/weights.json", "r") as f:
            weights = json.load(f)

    paper_engine = PaperTradingEngine()
    telegram = TelegramAlertEngine()

    if args.mode in ["morning", "intraday_search", "swing_search"]:
        print("=== Step 1: Fetching Dynamic Stock Universe ===")
        symbols = DynamicMarketFetcher.get_nifty_symbols("nifty50")
        market_data = DynamicMarketFetcher.fetch_live_market_data(symbols)

        print("=== Step 2: Running 5,200 Agent Swarm & Debate Engine ===")
        swarm = AgentSwarmCore(weights)
        analysis_results = swarm.run_swarm_analysis(market_data)

        top_intraday = analysis_results[:5]
        top_swing = analysis_results[:10]

        with open("data/predictions.json", "w") as f:
            json.dump({"top_intraday": top_intraday, "top_swing": top_swing}, f, indent=2)

        debate_logs = {item["symbol"]: item["debate"] for item in analysis_results[:10]}
        with open("data/debate_logs.json", "w") as f:
            json.dump(debate_logs, f, indent=2)

        print("=== Step 3: Executing Paper Trades & Sending Morning Telegram ===")
        paper_engine.execute_morning_allocation(top_intraday, top_swing)
        telegram.send_morning_alert(top_intraday, top_swing)

    elif args.mode == "evening":
        print("=== Step 1: Market Close Intraday Settlement ===")
        symbols = DynamicMarketFetcher.get_nifty_symbols("nifty50")
        market_data = DynamicMarketFetcher.fetch_live_market_data(symbols)

        daily_pnl = paper_engine.settle_intraday_market_close(market_data)

        print("=== Step 2: 4:00 PM Post-Market Retrospective & Retraining ===")
        retro = RetrospectiveEngine()
        completed = paper_engine.data.get("completed_trades", [])
        retro_result = retro.run_eod_retrospective(daily_pnl, completed)

        print("=== Step 3: Sending 4:15 PM EOD Telegram Report ===")
        telegram.send_evening_report(
            daily_pnl=daily_pnl, 
            profit_factor=retro_result["profit_factor"],
            summary="All intraday positions squared off. Overnight weights saved to repository."
        )

if __name__ == "__main__":
    main()
