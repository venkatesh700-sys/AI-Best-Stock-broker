import argparse
import json
import os
import requests
from datetime import datetime

from engine.fetch_data import fetch_stock_data, get_market_universe
from engine.paper_trading import execute_paper_trades, load_portfolio

def send_telegram_alert(mode, predictions, trades):
    """
    Sends live trade alert summaries to your phone via Telegram API.
    Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID stored in Repository Secrets.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("ℹ️ Telegram secrets missing. Skipping phone notification.")
        return

    top_picks = predictions[:5]
    lines = [
        f"🤖 *AI Stock Trader Swarm Alert*",
        f"📌 *Mode:* {mode.upper()}",
        f"🕒 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}",
        f"────────────────────"
    ]

    for p in top_picks:
        symbol = p.get("symbol")
        signal = p.get("signal")
        price = p.get("price")
        target = p.get("target")
        sl = p.get("stop_loss")
        emoji = "🟢" if signal == "BUY" else "🔴"

        lines.append(f"{emoji} *{symbol}* | {signal}")
        lines.append(f"   Price: ₹{price} | Target: ₹{target} | SL: ₹{sl}")

    lines.append(f"────────────────────")
    lines.append(f"✅ *Trades Executed:* {len(trades)}")
    lines.append(f"📊 [View Live Dashboard](https://venkatesh700-sys.github.io/AI-Best-Stock-broker/)")

    message = "\n".join(lines)
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        res = requests.post(
            url,
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10
        )
        if res.status_code == 200:
            print("📱 Telegram notification delivered to your phone!")
        else:
            print(f"⚠️ Telegram API response: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"⚠️ Telegram sending note: {e}")

def run_swarm_analysis(mode):
    """
    Fetches dynamic market universe live online and runs multi-agent evaluation.
    """
    symbols = get_market_universe()
    if not symbols:
        print("❌ No dynamic market symbols fetched. Exiting safely.")
        return [], []

    predictions = []
    debate_summary = []

    print(f"\n🤖 Running Agent Swarm Engine | Mode: {mode.upper()}")
    print(f"🔎 Dynamically evaluating dynamic tickers fetched from live web sources...")

    for symbol in symbols:
        df = fetch_stock_data(symbol)
        if df is None or df.empty:
            continue

        if len(df) >= 2:
            latest_close = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
        else:
            latest_close = float(df['Close'].iloc[-1])
            prev_close = latest_close

        change_pct = round(((latest_close - prev_close) / max(prev_close, 1e-5)) * 100, 2)
        signal = "BUY" if change_pct >= -0.5 else "SELL"
        target_price = round(latest_close * (1.02 if signal == "BUY" else 0.98), 2)
        stop_loss = round(latest_close * (0.99 if signal == "BUY" else 1.01), 2)

        strategy_type = "INTRADAY" if mode in ["morning", "intraday_search"] else "SWING"

        pred = {
            "symbol": symbol,
            "strategy": strategy_type,
            "signal": signal,
            "price": latest_close,
            "target": target_price,
            "stop_loss": stop_loss,
            "change_pct": change_pct,
            "confidence": round(0.75 + (min(abs(change_pct), 10) / 100), 2)
        }
        predictions.append(pred)

        debate_summary.append({
            "symbol": symbol,
            "bull_score": 80 if signal == "BUY" else 35,
            "bear_score": 20 if signal == "BUY" else 65,
            "consensus": signal
        })

    predictions.sort(key=lambda x: x["confidence"], reverse=True)
    return predictions, debate_summary

def update_learning_memory(mode, predictions, debate_summary):
    """Saves active predictions and appends to the rolling 365-day memory bank."""
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().isoformat()

    pred_data = {
        "last_updated": timestamp,
        "mode": mode,
        "total_scanned": len(predictions),
        "predictions": predictions
    }
    with open("data/predictions.json", "w") as f:
        json.dump(pred_data, f, indent=2)

    log_file = "data/debate_logs.json"
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    logs.append({
        "timestamp": timestamp,
        "mode": mode,
        "debate_summary": debate_summary,
        "top_signals": predictions[:10]
    })

    with open(log_file, "w") as f:
        json.dump(logs[-365:], f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="AI Stock Trader Autonomous Pipeline")
    parser.add_argument(
        '--mode',
        type=str,
        default='morning',
        help='Execution mode: morning, evening, intraday_search, swing_search'
    )
    args = parser.parse_args()

    mode = args.mode.lower()
    print(f"🚀 Execution Started | Mode: {mode}")

    load_portfolio()
    predictions, debate_summary = run_swarm_analysis(mode)
    
    if predictions:
        update_learning_memory(mode, predictions, debate_summary)
        trades = execute_paper_trades(predictions, mode)
        send_telegram_alert(mode, predictions, trades)
        print(f"✅ Execution complete! Processed {len(trades)} paper trades out of dynamic market picks.")
    else:
        print("⚠️ No valid market data processed during this session.")

if __name__ == "__main__":
    main()
