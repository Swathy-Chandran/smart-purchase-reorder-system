def detect_anomalies(sales_df):
    """
    Output:
    {
        item_id: {
            message
        }
    }
    """

    anomalies = {}

    for item_id, group in sales_df.groupby("item_id"):
        if group["qty"].std() and group["qty"].std() > 40:
            anomalies[item_id] = {
                "message": "Unusual stock depletion detected"
            }

    return anomalies
