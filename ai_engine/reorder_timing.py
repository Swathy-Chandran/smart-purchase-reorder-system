def predict_reorder_timing(item_id, stock, demand_behavior, risk, supplier):
    """
    Output:
    {
        reorder_in_days,
        confidence
    }
    """

    stockout_prob = risk.get("stockout_probability", 0.0)

    if stockout_prob >= 0.7:
        days = 5
        confidence = "High"
    elif stockout_prob >= 0.5:
        days = 10
        confidence = "Medium"
    else:
        days = 15
        confidence = "Low"

    return {
        "reorder_in_days": days,
        "confidence": confidence
    }
