# ==========================================================
# Demand Behavior Analyzer (SAFE, STABLE, UI-READY)
# ==========================================================

import pandas as pd


def analyze_demand_behavior(sales_df: pd.DataFrame) -> dict:
    """
    Analyzes demand behavior for ONE item.

    Input:
        sales_df columns REQUIRED:
        - date
        - total_qty

    Output (UI-ready):
        {
            baseline_level: Very High / High / Medium / Low
            demand_trend: Increasing / Stable / Decreasing
            volatility: High / Medium / Low
        }
    """

    # ================================
    # SAFETY CHECK (CRITICAL FIX)
    # ================================
    if sales_df is None or sales_df.empty:
        return {
            "baseline_level": "Low",
            "demand_trend": "Stable",
            "volatility": "Low",
        }

    # ================================
    # ENSURE NUMERIC
    # ================================
    sales_df = sales_df.copy()
    sales_df["total_qty"] = pd.to_numeric(
        sales_df["total_qty"], errors="coerce"
    ).fillna(0)

    # ================================
    # BASELINE LEVEL
    # ================================
    avg_demand = sales_df["total_qty"].mean()

    if avg_demand > 50:
        baseline = "Very High"
    elif avg_demand > 30:
        baseline = "High"
    elif avg_demand > 15:
        baseline = "Medium"
    else:
        baseline = "Low"

    # ================================
    # DEMAND TREND
    # ================================
    sales_df = sales_df.sort_values("date")

    if len(sales_df) >= 2:
        first_half = sales_df.iloc[: len(sales_df) // 2]["total_qty"].mean()
        second_half = sales_df.iloc[len(sales_df) // 2 :]["total_qty"].mean()

        if second_half > first_half * 1.1:
            trend = "Increasing"
        elif second_half < first_half * 0.9:
            trend = "Decreasing"
        else:
            trend = "Stable"
    else:
        trend = "Stable"

    # ================================
    # VOLATILITY
    # ================================
    std_dev = sales_df["total_qty"].std()

    if std_dev > avg_demand * 0.6:
        volatility = "High"
    elif std_dev > avg_demand * 0.3:
        volatility = "Medium"
    else:
        volatility = "Low"

    # ================================
    # FINAL OUTPUT
    # ================================
    return {
        "baseline_level": baseline,
        "demand_trend": trend,
        "volatility": volatility,
    }
