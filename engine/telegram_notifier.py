import os
import requests

class TelegramAlertEngine:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    def send_message(self, message):
        if not self.token or not self.chat_id:
            print("[Telegram Warning] Bot Token or Chat ID missing. Skipping alert.")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            return res.status_code == 200
        except Exception as e:
            print(f"[Telegram Error] Failed to send message: {e}")
            return False

    def send_morning_alert(self, top_intraday, top_swing):
        msg = "🚀 *AI: The Best Stock Trader — Morning Signal* 🚀\n\n"
        msg += "📈 *TOP 5 INTRADAY PICKS*\n"
        for i, s in enumerate(top_intraday[:5], 1):
            msg += f"{i}. *{s['symbol']}* | Entry: ₹{s['entry_price']} | Tgt: ₹{s['target_price']} | SL: ₹{s['stop_loss']}\n"

        msg += "\n📊 *TOP 10 SWING OPPORTUNITIES*\n"
        for i, s in enumerate(top_swing[:10], 1):
            msg += f"{i}. *{s['symbol']}* | Entry: ₹{s['entry_price']} | Tgt: ₹{s['target_price']} | Conf: {s['confidence']}%\n"

        msg += "\n_Automated Execution Initiated across Paper Portfolios._"
        return self.send_message(msg)

    def send_evening_report(self, daily_pnl, profit_factor, summary):
        msg = "📊 *AI: The Best Stock Trader — 4:15 PM EOD Report* 📊\n\n"
        msg += f"💰 *Realized Daily Intraday P&L:* ₹{daily_pnl:+,.2f}\n"
        msg += f"🎯 *Target Profit Factor:* {profit_factor} (Target >= 1.5)\n"
        msg += f"🧠 *Overnight Retraining:* Complete\n\n"
        msg += f"📝 *Takeaway:* {summary}"
        return self.send_message(msg)
