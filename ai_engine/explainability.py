
# =====================================================
# EXPLAINABLE AI MODULE
# =====================================================

def explain_decision(final_decision):
    """
    Generates human-readable explanation for AI decision
    """

    explanations = []

    # Demand explanation
    explanations.append(
        f"Baseline demand level is {final_decision['demand_level']}."
    )

    # Risk explanation
    risk = final_decision["stockout_risk"]
    if risk >= 0.8:
        explanations.append(
            "Stockout risk is very high due to insufficient inventory."
        )
    elif risk >= 0.5:
        explanations.append(
            "Stockout risk is moderate based on projected demand."
        )
    else:
        explanations.append(
            "Stock levels are currently sufficient."
        )

    # Timing explanation
    action = final_decision["action"]
    if action["reorder_in_days"] <= 2:
        explanations.append(
            "Immediate reorder is recommended to prevent stockouts."
        )
    else:
        explanations.append(
            "Reorder can be planned in advance without urgency."
        )

    # Quantity explanation
    explanations.append(
        f"Recommended reorder quantity is {action['quantity']} units, "
        "calculated using EOQ adjusted by demand, risk, and supplier reliability."
    )

    # Safety stock
    if action["safety_stock"] == "Increased":
        explanations.append(
            "Safety stock is increased due to high risk and demand uncertainty."
        )

    return explanations
