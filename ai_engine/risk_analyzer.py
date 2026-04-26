def analyze_inventory_risk(item_id, stock, demand_behavior, seasonality):
    seasonal_boost = seasonality.get("seasonal_boost", 0)

    stockout_prob = round(min(1.0, 0.4 + seasonal_boost / 100), 2)

    risk_level = (
        "HIGH" if stockout_prob > 0.7 else
        "MEDIUM" if stockout_prob > 0.4 else
        "LOW"
    )

    reasons = []
    if seasonal_boost > 15:
        reasons.append("High seasonal demand")
    if demand_behavior["demand_trend"] == "Increasing":
        reasons.append("Consumption trend increasing")

    return {
        "stockout_probability": stockout_prob,
        "risk_level": risk_level,
        "overall_score": round(stockout_prob * 0.9, 2),
        "reasons": reasons
    }
