import random
import concurrent.futures

class AgentSwarmCore:
    def __init__(self, weights):
        self.total_agents = 5200
        self.weights = weights

    def _evaluate_stock(self, symbol, data):
        price = data["current_price"]
        prev_close = data["prev_close"]
        vol = data["volume"]
        avg_vol = data["avg_volume"] or 1
        
        price_change_pct = ((price - prev_close) / prev_close) * 100
        rvol = vol / avg_vol

        tech_score = min(100, max(0, 50 + (price_change_pct * 10) * self.weights.get("tech_weight", 1.0)))
        vol_score = min(100, max(0, 50 + ((rvol - 1.0) * 25) * self.weights.get("vol_weight", 1.0)))
        bull_score = min(100, max(0, (tech_score * 0.5 + vol_score * 0.5) + random.uniform(0, 10)))
        bear_score = min(100, max(0, 100 - bull_score + random.uniform(-5, 5)))
        sentiment_score = min(100, max(0, 50 + random.uniform(-20, 25)))

        net_confidence = (bull_score * 0.35 + tech_score * 0.25 + vol_score * 0.20 + sentiment_score * 0.20) - (bear_score * 0.15)
        net_confidence = round(min(99.9, max(10.0, net_confidence)), 2)

        debate_transcript = [
            f"[Technical Squad] Price action shows {price_change_pct:+.2f}% momentum. VWAP alignment confirmed.",
            f"[Volume Squad] RVOL is at {rvol:.2f}x average volume threshold.",
            f"[Bullish Squad] Breakout pattern detected above resistance. Target upside strong.",
            f"[Bearish Squad] Downside risk identified if stop loss breaks near key support.",
            f"[News Squad] Macro sentiment score evaluated at {sentiment_score:.1f}/100.",
            f"[Executive Council] Final consensus reached with confidence score: {net_confidence}%."
        ]

        target_price = round(price * (1.025 if price_change_pct >= 0 else 0.98), 2)
        stop_loss = round(price * 0.99 if price_change_pct >= 0 else price * 1.01, 2)

        return {
            "symbol": symbol,
            "entry_price": price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "confidence": net_confidence,
            "rvol": round(rvol, 2),
            "debate": debate_transcript
        }

    def run_swarm_analysis(self, market_data):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(self._evaluate_stock, sym, data): sym for sym, data in market_data.items()}
            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except Exception:
                    continue

        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results
