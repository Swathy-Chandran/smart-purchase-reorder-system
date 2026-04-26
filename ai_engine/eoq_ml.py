def compute_eoq_ml(item_id, demand_behavior, seasonality, risk, supplier):
    """
    Output:
    {
        recommended_quantity
    }
    """

    base_qty = 200

    if demand_behavior.get("baseline_level") == "Very High":
        base_qty += 100

    if risk.get("risk_level") == "HIGH":
        base_qty += 60

    return {
        "recommended_quantity": base_qty
    }
