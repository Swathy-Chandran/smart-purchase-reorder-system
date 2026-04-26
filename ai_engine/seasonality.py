import pandas as pd


def analyze_seasonality(sales_df):
    """
    Learns seasonality from historical data
    and predicts boost for future months.
    """

    if sales_df.empty:
        return {}

    sales_df["month_num"] = sales_df["month"].dt.month

    seasonal = (
        sales_df
        .groupby(["item_id", "month_num"])["quantity"]
        .mean()
        .reset_index()
    )

    seasonality = {}
    for _, row in seasonal.iterrows():
        seasonality.setdefault(row["item_id"], {})
        seasonality[row["item_id"]][row["month_num"]] = {
            "seasonal_boost": round((row["quantity"] / seasonal["quantity"].mean() - 1) * 100, 2),
            "expected_level": "Very High" if row["quantity"] > seasonal["quantity"].mean() else "Medium"
        }

    return seasonality
