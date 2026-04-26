import pandas as pd
from django.utils import timezone
from datetime import timedelta
from reorder_app.models import ConsumptionReport, Product


def load_sales_data(selected_month):
    """
    ✅ ALWAYS load historical data (last 12 months)
    NOT selected month data.
    """

    end_date = timezone.now()
    start_date = end_date - timedelta(days=365)

    qs = ConsumptionReport.objects.filter(
        start_date__gte=start_date,
        end_date__lte=end_date
    )

    if not qs.exists():
        return pd.DataFrame()

    data = []
    for r in qs:
        data.append({
            "item_id": r.product_id,
            "date": r.end_date,
            "quantity": r.quantity_consumed
        })

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()

    return df


def load_current_stock(_):
    """
    Stock is current, not month-based.
    """
    stock = {}
    for p in Product.objects.all():
        stock[p.id] = int(getattr(p, "stock_quantity", 0) or 0)
    return stock
