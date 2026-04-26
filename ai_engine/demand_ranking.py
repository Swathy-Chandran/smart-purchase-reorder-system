def rank_item_demand(sales_df):
    ranking = []

    for item_id, df in sales_df.groupby("item_id"):
        avg = df["quantity"].mean()
        level = "Very High" if avg > 80 else "High" if avg > 50 else "Medium"

        ranking.append({"item_id": item_id, "level": level})

    return sorted(ranking, key=lambda x: ["Very High", "High", "Medium"].index(x["level"]))
