"""
FINAL AI DECISION ENGINE
Combines all AI outputs into a single explainable decision
"""

from reorder_app.ai_engine.demand_behavior import analyze_demand_behavior
from reorder_app.ai_engine.seasonality import analyze_seasonality
from reorder_app.ai_engine.risk_analyzer import analyze_inventory_risk
from reorder_app.ai_engine.supplier_analyzer import analyze_supplier_risk
from reorder_app.ai_engine.reorder_timing import predict_reorder_timing
from reorder_app.ai_engine.eoq_ml import compute_eoq_ml
from reorder_app.ai_engine.anomaly_detector import detect_anomalies


def run_final_decision(item_id, sales_df, stock, month):
    """
    FINAL OUTPUT USED BY service.py

    Returns:
    {
        decision,
        risk_level,
        explanation
    }
    """

    # ---------- Demand ----------
    demand_behavior_all = analyze_demand_behavior(sales_df)
    demand_behavior = demand_behavior_all.get(item_id, {})

    # ---------- Seasonality ----------
    seasonality_all = analyze_seasonality(sales_df)
    seasonality = seasonality_all.get(item_id, {}).get(month, {})

    # ---------- Risk ----------
    risk = analyze_inventory_risk(
        item_id=item_id,
        stock=stock,
        demand_behavior=demand_behavior,
        seasonality=seasonality
    )

    # ---------- Supplier ----------
    supplier = analyze_supplier_risk(item_id)

    # ---------- Timing ----------
    timing = predict_reorder_timing(
        item_id=item_id,
        stock=stock,
        demand_behavior=demand_behavior,
        risk=risk,
        supplier=supplier
    )

    # ---------- Quantity ----------
    quantity = compute_eoq_ml(
        item_id=item_id,
        demand_behavior=demand_behavior,
        seasonality=seasonality,
        risk=risk,
        supplier=supplier
    )

    # ---------- Decision ----------
    decision = "REORDER" if risk["risk_level"] in ["HIGH", "MEDIUM"] else "HOLD"

    explanation = [
        f"For selected month, demand trend is {demand_behavior.get('demand_trend', 'Stable')}.",
        f"Stockout probability is {risk.get('stockout_probability')}.",
        f"Supplier lead time is {supplier.get('predicted_lead_time')} days.",
        f"Recommended reorder quantity is {quantity.get('recommended_quantity')} units.",
    ]

    return {
        "decision": decision,
        "risk_level": risk["risk_level"],
        "reorder_in_days": timing["reorder_in_days"],
        "recommended_quantity": quantity["recommended_quantity"],
        "explanation": explanation
    }
