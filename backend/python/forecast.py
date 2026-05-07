"""ForecastEngine — reads {store, sales[], products[]} from stdin, writes JSON forecast."""
import sys, json
from collections import defaultdict
from statistics import mean

def forecast(payload):
    sales = payload.get("sales", [])
    products = payload.get("products", [])
    by_product = defaultdict(list)
    for s in sales:
        by_product[s["product"]].append(s.get("actual_sales", 0) or 0)

    forecasts = []
    for p in products:
        hist = by_product.get(p["name"], [])
        avg = mean(hist) if hist else max(p.get("reorder_level", 10), 10)
        # simple trend: last 3 vs prev 3
        trend = 1.0
        if len(hist) >= 6:
            last3 = mean(hist[-3:]); prev3 = mean(hist[-6:-3]) or 1
            trend = max(0.5, min(1.5, last3 / prev3))
        predicted = round(avg * 1.05 * trend)
        forecasts.append({
            "product": p["name"],
            "current_stock": p.get("current_stock", 0),
            "reorder_level": p.get("reorder_level", 0),
            "avg_daily_demand": round(avg, 2),
            "trend_factor": round(trend, 2),
            "predicted_demand": predicted,
            "shortfall": max(0, predicted - p.get("current_stock", 0)),
        })
    return {"store": payload.get("store"), "forecasts": forecasts}

if __name__ == "__main__":
    data = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(forecast(data)))
