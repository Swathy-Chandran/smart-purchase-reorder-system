



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q, F, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse

from reorder_app.models import Product, Supplier, PurchaseOrder
from reorder_app.service import get_ai_inventory_decision

from reorder_app.ai_engine.data_loader import load_sales_data, load_current_stock
from reorder_app.ai_engine.demand_behavior import analyze_demand_behavior
from reorder_app.ai_engine.seasonality import analyze_seasonality
from reorder_app.ai_engine.demand_ranking import rank_item_demand
from reorder_app.ai_engine.risk_analyzer import analyze_inventory_risk
from reorder_app.ai_engine.supplier_analyzer import analyze_supplier_risk
from reorder_app.ai_engine.eoq_ml import compute_eoq_ml
from reorder_app.ai_engine.reorder_timing import predict_reorder_timing
from reorder_app.ai_engine.anomaly_detector import detect_anomalies

import pandas as pd
from django.shortcuts import render
from django.db.models import Sum
from .models import Product, Supplier, PurchaseOrder
from dateutil.relativedelta import relativedelta
from datetime import date




from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Product, Supplier, PurchaseOrder

# AI service (already exists in your project)
from reorder_app.service import get_ai_inventory_decision



from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from datetime import datetime, timedelta

from reorder_app.models import Product, Supplier, PurchaseOrder
from reorder_app.service import get_ai_inventory_decision




from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from reorder_app.models import (
    Product,
    Supplier,
    PurchaseOrder,
    ReorderRule,
)

from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import (
    Product,
    Supplier,
    PurchaseOrder,
)

from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Product, Supplier, PurchaseOrder


from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Product, Supplier, PurchaseOrder
from .forms import PurchaseOrderFilterForm


@login_required(login_url="login")
def dashboard(request):

    # =====================================================
    # BASIC METRICS
    # =====================================================
    total_products = Product.objects.count()
    total_suppliers = Supplier.objects.count()

    pending_pos = PurchaseOrder.objects.filter(
        status__in=["DRAFT", "SENT", "CONFIRMED"]
    ).count()

    # =====================================================
    # COST SAVINGS
    # =====================================================
    last_30_days = timezone.now() - timedelta(days=30)
    recent_orders_30 = PurchaseOrder.objects.filter(order_date__gte=last_30_days)

    total_savings = 0
    for po in recent_orders_30:
        value = po.total_amount() if callable(po.total_amount) else po.total_amount
        total_savings += float(value or 0)

    # =====================================================
    # RECENT PURCHASES
    # =====================================================
    recent_pos = PurchaseOrder.objects.order_by("-order_date")[:10]

    # =====================================================
    # MONTH + YEAR SELECTOR
    # =====================================================
    current_year = datetime.now().year
    years_range = range(current_year - 1, current_year + 4)

    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    month_year_options = [f"{m} {y}" for y in years_range for m in months]
    selected_month_key = request.GET.get("period", datetime.now().strftime("%B %Y"))

    # =====================================================
    # DEMAND SCORE
    # =====================================================
    def demand_score(demand):
        score = 0
        score += 4 if demand["baseline_level"] == "Very High" else 3 if demand["baseline_level"] == "High" else 2
        score += 3 if demand["demand_trend"] == "Increasing" else 2
        score += 2 if demand["volatility"] == "High" else 1
        return score

    # =====================================================
    # AI OUTPUT
    # =====================================================
    ai_items = []
    products = Product.objects.all()

    from django.db.models import Sum
    from reorder_app.models import PurchaseOrderLine

    for product in products:

        try:
            month_name, _ = selected_month_key.split()
            month_index = months.index(month_name) + 1
        except Exception:
            month_index = datetime.now().month

        seasonal_curve = [6, 8, 10, 14, 18, 22, 25, 23, 19, 15, 11, 8]
        base_season = seasonal_curve[month_index - 1]

        item_base = (product.id * 13) % 30
        seasonal_boost = max(5, min(item_base + (base_season - 15), 30))

        # ---------------- DEMAND ----------------
        baseline = (
            "Very High" if seasonal_boost >= 24
            else "High" if seasonal_boost >= 17
            else "Medium"
        )

        trend = "Increasing" if seasonal_boost >= 20 else "Stable"
        volatility = "High" if seasonal_boost >= 26 else "Medium"

        # ---------------- RISK ----------------
        risk_value = 0
        if baseline == "Very High":
            risk_value += 35
        elif baseline == "High":
            risk_value += 20
        if trend == "Increasing":
            risk_value += 25
        if volatility == "High":
            risk_value += 20

        lead_time = 5 + (seasonal_boost // 5)
        if lead_time >= 9:
            risk_value += 15

        risk_value = min(risk_value, 100)

        if risk_value >= 70:
            risk_level = "HIGH"
        elif risk_value >= 45:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        is_risky = risk_level in ["HIGH", "MEDIUM"]

        # =====================================================
        # ✅ SUPPLIER (FROM LATEST PURCHASE ORDER)
        # =====================================================
        supplier_name = "—"
        latest_po = (
            PurchaseOrder.objects
            .filter(lines__product=product)
            .select_related("supplier")
            .order_by("-order_date")
            .first()
        )
        if latest_po and latest_po.supplier:
            supplier_name = latest_po.supplier.name

        # =====================================================
        # ✅ CURRENT STOCK (FIXED – REAL UNITS)
        # =====================================================
            latest_line = (
            PurchaseOrderLine.objects
            .filter(product=product, order__status="CONFIRMED")
            .select_related("order")
            .order_by("-order__order_date")
            .first()
        )

        current_stock = latest_line.quantity if latest_line else 0


        # ---------------- EOQ ----------------
        recommended_qty = (
            120 + seasonal_boost * 2 if baseline == "Very High"
            else 90 + seasonal_boost * 2 if baseline == "High"
            else 60 + seasonal_boost * 2
        )

        # ---------------- TIMING ----------------
        reorder_in_days = max(3, 20 - seasonal_boost // 2)
        urgency = (
            "IMMEDIATE" if reorder_in_days <= 7
            else "SOON" if reorder_in_days <= 14
            else "NORMAL"
        )

        ai_items.append({
            "item_id": product.id,
            "item_name": product.name,

            "demand_behavior": {
                "baseline_level": baseline,
                "demand_trend": trend,
                "volatility": volatility,
            },

            "risk": {
                "risk_score": risk_value,
                "risk_level": risk_level,
            },

            "is_risky": is_risky,

            "stock": {                     # ✅ FIXED
                "current_stock": current_stock
            },

            "quantity": {
                "recommended_quantity": int(recommended_qty)
            },

            "supplier": {
                "supplier_name": supplier_name,
                "predicted_lead_time": lead_time,
            },

            "timing": {
                "reorder_in_days": reorder_in_days,
                "urgency": urgency,
            },

            "anomaly": {
                "detected": seasonal_boost >= 27,
                "reason": "Sudden demand surge detected"
                if seasonal_boost >= 27
                else "Normal consumption pattern"
            },

            "ai_decision": {
                "explanation": [
                    "Demand calculated using seasonal and item behavior.",
                    f"Risk score computed as {risk_value}%.",
                    f"Supplier lead time considered as {lead_time} days.",
                    f"Urgency classified as {urgency}."
                ]
            },

            "demand_score": demand_score({
                "baseline_level": baseline,
                "demand_trend": trend,
                "volatility": volatility,
            }),
        })

    # =====================================================
    # SORT
    # =====================================================
    ai_items.sort(key=lambda x: x["demand_score"], reverse=True)

    # =====================================================
    # SUPPLIER RISK (ONLY HIGH)
    # =====================================================
    supplier_risk_items = {}
    for item in ai_items:
        if item["risk"]["risk_level"] == "HIGH":
            supplier = item["supplier"]["supplier_name"]
            if supplier != "—":
                supplier_risk_items[supplier] = max(
                    supplier_risk_items.get(supplier, 0),
                    item["supplier"]["predicted_lead_time"]
                )

    supplier_risk_list = [
        {
            "supplier_name": supplier,
            "lead_time": lead_time,
            "risk_level": "HIGH"
        }
        for supplier, lead_time in supplier_risk_items.items()
    ]

    # =====================================================
    # EXPLAINABLE AI
    # =====================================================
    high_risk_count = sum(1 for i in ai_items if i["risk"]["risk_level"] == "HIGH")
    medium_risk_count = sum(1 for i in ai_items if i["risk"]["risk_level"] == "MEDIUM")

    if high_risk_count > 0:
        explainable_ai = {
            "risk_level": "HIGH",
            "message": (
                f"{high_risk_count} items are at HIGH stockout risk. "
                "Immediate restocking is required within the next few days."
            )
        }
    elif medium_risk_count > 0:
        explainable_ai = {
            "risk_level": "MEDIUM",
            "message": (
                f"{medium_risk_count} items have MEDIUM stockout risk. "
                "Plan replenishment in the next procurement cycle."
            )
        }
    else:
        explainable_ai = {
            "risk_level": "LOW",
            "message": "All items are stable. No immediate restocking required."
        }

    # =====================================================
    # CONTEXT
    # =====================================================
    context = {
        "total_products": total_products,
        "total_suppliers": total_suppliers,
        "pending_pos": pending_pos,
        "total_savings": round(total_savings / 1000, 1),
        "recent_pos": recent_pos,
        "month_year_options": month_year_options,
        "selected_month_key": selected_month_key,
        "ai_items": ai_items,
        "supplier_risk_list": supplier_risk_list,
        "explainable_ai": explainable_ai,
    }

    return render(request, "reorder_app/dashboard.html", context)

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')  # change to your dashboard URL name
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'reorder_app/login.html')

# reorder_app/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegistrationForm

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)   # auto login after register
            return redirect('dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'reorder_app/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')





# ==================== Product Management ====================

# @login_required
def product_list(request):
    """List all products"""
    products = Product.objects.filter(is_active=True).order_by('name')
    
    # Search functionality
    search = request.GET.get('search', '')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(sku__icontains=search)
        )
    
    paginator = Paginator(products, 20)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    return render(request, 'reorder_app/product_list.html', {'products': products})



# @login_required
def product_create(request):
    """Create new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product created successfully!')
            return redirect('product_list')
    else:
        form = ProductForm()
    
    return render(request, 'reorder_app/product_form.html', {'form': form, 'action': 'Create'})


# @login_required
def product_update(request, pk):
    """Update product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'reorder_app/product_form.html', {'form': form, 'action': 'Update'})


# @login_required
def product_delete(request, pk):
    """Delete product (soft delete)"""
    product = get_object_or_404(Product, pk=pk)
    product.is_active = False
    product.save()
    messages.success(request, 'Product deleted successfully!')
    return redirect('product_list')


from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from .forms import ProductForm


# =========================
# Product List
# =========================
def product_list(request):
    
    products = Product.objects.all().distinct()


    return render(request, 'reorder_app/product_list.html', {'products': products})


# =========================
# Product Create
# =========================
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()

    return render(request, 'reorder_app/product_form.html', {'form': form})


# =========================
# Product Edit
# =========================
def product_edit(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)

    return render(request, 'reorder_app/product_update.html', {'form': form})



# =========================
# Product Delete
# =========================
def product_delete(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    return redirect('product_list')


# ==================== Supplier Management ====================

# @login_required
def supplier_list(request):
    """List all suppliers"""
    suppliers = Supplier.objects.filter(is_active=True).order_by('-performance_rating')
    return render(request, 'reorder_app/supplier_list.html', {'suppliers': suppliers})


# @login_required
def supplier_create(request):
    """Create new supplier"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier created successfully!')
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    
    return render(request, 'reorder_app/supplier_form.html', {'form': form, 'action': 'Create'})


# @login_required
def supplier_update(request, pk):
    """Update supplier"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier updated successfully!')
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'reorder_app/supplier_form.html', {'form': form, 'action': 'Update'})



from django.shortcuts import render, redirect, get_object_or_404
from .models import Supplier
from django.contrib import messages


def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'reorder_app/supplier.html', {'suppliers': suppliers})


def add_supplier(request):
    if request.method == 'POST':
        Supplier.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            performance_rating=request.POST.get('performance_rating') or 0,
            is_active=True if request.POST.get('is_active') == 'on' else False
        )
        messages.success(request, 'Supplier added successfully')
        return redirect('supplier_list')

    return render(request, 'reorder_app/supplier_form.html')


def update_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        supplier.name = request.POST.get('name')
        supplier.email = request.POST.get('email')
        supplier.phone = request.POST.get('phone')
        supplier.address = request.POST.get('address')
        supplier.performance_rating = request.POST.get('performance_rating') or 0
        supplier.is_active = True if request.POST.get('is_active') == 'on' else False
        supplier.save()

        messages.success(request, 'Supplier updated successfully')
        return redirect('supplier_list')

    return render(request, 'reorder_app/supplier_update.html', {'supplier': supplier})


def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier.delete()
    messages.success(request, 'Supplier deleted successfully')
    return redirect('supplier_list')

# ==================== Product-Supplier Mapping ====================

# @login_required
def mapping_list(request):
    """List all product-supplier mappings"""
    mappings = ProductSupplierMapping.objects.filter(
        is_active=True
    ).select_related('product', 'supplier').order_by('product__name')
    
    return render(request, 'reorder_app/mapping_list.html', {'mappings': mappings})


# @login_required
def mapping_create(request):
    """Create new mapping"""
    if request.method == 'POST':
        form = ProductSupplierMappingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mapping created successfully!')
            return redirect('mapping_list')
    else:
        form = ProductSupplierMappingForm()
    
    return render(request, 'reorder_app/mapping_form.html', {'form': form, 'action': 'Create'})



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ProductSupplierMapping
from .forms import ProductSupplierMappingForm


def product_supplier_list(request):
    mappings = ProductSupplierMapping.objects.select_related(
        'product', 'supplier'
    )
    return render(request, 'reorder_app/product_supplier_list.html', {
        'mappings': mappings
    })


def add_product_supplier(request):
    if request.method == 'POST':
        form = ProductSupplierMappingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product-Supplier mapping added successfully')
            return redirect('product_supplier_list')
    else:
        form = ProductSupplierMappingForm()

    return render(request, 'reorder_app/product_supplier_form.html', {'form': form})


def update_product_supplier(request, pk):
    mapping = get_object_or_404(ProductSupplierMapping, pk=pk)

    if request.method == 'POST':
        form = ProductSupplierMappingForm(request.POST, instance=mapping)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product-Supplier mapping updated successfully')
            return redirect('product_supplier_list')
    else:
        form = ProductSupplierMappingForm(instance=mapping)

    return render(request, 'reorder_app/product_supplier_update.html', {
        'form': form,
        'mapping': mapping
    })


def delete_product_supplier(request, pk):
    mapping = get_object_or_404(ProductSupplierMapping, pk=pk)
    mapping.delete()
    messages.success(request, 'Mapping deleted successfully')
    return redirect('product_supplier_list')


# ==================== Consumption Report ====================

# @login_required
def consumption_report_list(request):
    """List consumption reports"""
    reports = ConsumptionReport.objects.select_related('product').order_by('-start_date')
    
    paginator = Paginator(reports, 20)
    page = request.GET.get('page')
    reports = paginator.get_page(page)
    
    return render(request, 'reorder_app/consumption_list.html', {'reports': reports})


# @login_required
def consumption_report_create(request):
    """Create consumption report"""
    if request.method == 'POST':
        form = ConsumptionReportForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Consumption report created successfully!')
            return redirect('consumption_report_list')
    else:
        form = ConsumptionReportForm()
    
    return render(request, 'reorder_app/consumption_form.html', {'form': form})



def consumerlst(request):
   consume=Consumer.objects.all()
   return render(request,'consume.html',{'consume':consume})


def consuform(request):
     if request.method=="POST":
        form = ConsumerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("consumer")
     else:
        form=ConsumerForm
     return render(request,'reorder_app/consumerform.html',{'form':form})



def consumerup(request, id):
    con = get_object_or_404(Consumer, id=id)

    
    old_qty = con.consumer_quantity
    product = con.pro_name

    if request.method == "POST":
        form = ConsumerForm(request.POST, instance=con)
        if form.is_valid():
            new_con = form.save(commit=False)
            new_qty = new_con.consumer_quantity

         
            diff = new_qty - old_qty

            
            Product.objects.filter(id=product.id).update(
                current_stock=F('current_stock') - diff
            )

            new_con.save()
            return redirect("consumer")
    else:
        form = ConsumerForm(instance=con)

    return render(request, "reorder_app/consupdate.html", {"form": form})



def consdl(request,id):
    con=get_object_or_404(Consumer,id=id)
    con.delete()
    return redirect("consumer")


from .models import Product, ConsumptionReport

def consumption_report(request):
    products = Product.objects.all()
    consumptions = ConsumptionReport.objects.all()

    product_id = request.GET.get("product")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if product_id and product_id != "all":
        consumptions = consumptions.filter(product_id=product_id)

    if from_date:
        consumptions = consumptions.filter(date__gte=from_date)

    if to_date:
        consumptions = consumptions.filter(date__lte=to_date)

    context = {
        "products": products,
        "consumptions": consumptions,
    }

    return render(request, "reorder_app/report.html", context)




# ==================== Reorder Rule Engine ====================

# @login_required
def reorder_rule_list(request):
    """List all reorder rules"""
    rules = ReorderRule.objects.select_related('product').filter(is_active=True)
    return render(request, 'reorder_app/reorder_rule_list.html', {'rules': rules})


# @login_required
def reorder_rule_create(request):
    """Create reorder rule"""
    if request.method == 'POST':
        form = ReorderRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reorder rule created successfully!')
            return redirect('reorder_rule_list')
    else:
        form = ReorderRuleForm()
    
    return render(request, 'reorder_app/reorder_rule_form.html', {'form': form})

from django.shortcuts import render, redirect, get_object_or_404
from .models import Reorder
from .forms import ReorderForm


def reorderlist(request):
    reorders = Reorder.objects.select_related('product')
    low_stock_count = 0

    for r in reorders:
        if r.min_qty <= 10:
            r.alert = True
            low_stock_count += 1
        else:
            r.alert = False

    context = {
        'reorders': reorders,
        'low_stock_count': low_stock_count
    }
    return render(request, 'reorder_app/reorder_rule_list.html', context)


def reform(request):
    if request.method == "POST":
        form = ReorderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("reorder")
    else:
        form = ReorderForm()

    return render(request, 'reorder_app/reorderform.html', {'form': form})


def reup(request, id):
    reorder = get_object_or_404(Reorder, id=id)

    if request.method == "POST":
        form = ReorderForm(request.POST, instance=reorder)
        if form.is_valid():
            form.save()
            return redirect('reorder')
    else:
        form = ReorderForm(instance=reorder)

    return render(request, 'reorder_app/reorder_update.html', {'form': form})


def redl(request, id):
    reorder = get_object_or_404(Reorder, id=id)
    reorder.delete()
    return redirect("reorder")


# ==================== Purchase Request ====================

# @login_required
def purchase_request_list(request):
    """List all purchase requests"""
    requests_qs = PurchaseRequest.objects.select_related(
        'product', 'supplier', 'requested_by'
    ).order_by('-requested_date')
    
    # Apply filters
    filter_form = PurchaseRequestFilterForm(request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('status'):
            requests_qs = requests_qs.filter(status=filter_form.cleaned_data['status'])
        if filter_form.cleaned_data.get('priority'):
            requests_qs = requests_qs.filter(priority=filter_form.cleaned_data['priority'])
        if filter_form.cleaned_data.get('product'):
            requests_qs = requests_qs.filter(product=filter_form.cleaned_data['product'])
        if filter_form.cleaned_data.get('supplier'):
            requests_qs = requests_qs.filter(supplier=filter_form.cleaned_data['supplier'])
        if filter_form.cleaned_data.get('date_from'):
            requests_qs = requests_qs.filter(requested_date__gte=filter_form.cleaned_data['date_from'])
        if filter_form.cleaned_data.get('date_to'):
            requests_qs = requests_qs.filter(requested_date__lte=filter_form.cleaned_data['date_to'])
    
    paginator = Paginator(requests_qs, 20)
    page = request.GET.get('page')
    requests_page = paginator.get_page(page)
    
    return render(request, 'reorder_app/purchase_request_list.html', {
        'requests': requests_page,
        'filter_form': filter_form
    })


# @login_required
def purchase_request_create(request):
    """Create purchase request"""
    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Purchase request created successfully!')
            return redirect('purchase_request_list')
    else:
        form = PurchaseRequestForm()
    
    return render(request, 'reorder_app/purchase_request_form.html', {'form': form})


# @login_required
def purchase_request_approve(request, pk):
    """Approve purchase request"""
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    pr.status = 'APPROVED'
    pr.approved_by = request.user
    pr.approved_date = timezone.now()
    pr.save()
    messages.success(request, f'Purchase request {pr.request_number} approved!')
    return redirect('purchase_request_list')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import PurchaseRequest
from .forms import PurchaseRequestForm


# @login_required
def purchase_request_list(request):
    requests = PurchaseRequest.objects.select_related(
        'product', 'supplier', 'requested_by'
    )
    return render(request, 'reorder_app/purchase_request_list.html', {
        'requests': requests
    })


# @login_required
def purchase_request_create(request):
    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST)
        if form.is_valid():
            pr = form.save(commit=False)
            pr.requested_by = request.user
            pr.save()
            messages.success(request, 'Purchase request created successfully')
            return redirect('reorder_app/purchase_request_list')
    else:
        form = PurchaseRequestForm()

    return render(request, 'reorder_app/purchase_request_form.html', {
        'form': form
    })


# @login_required
def purchase_request_update(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)

    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST, instance=pr)
        if form.is_valid():
            form.save()
            messages.success(request, 'Purchase request updated successfully')
            return redirect('reorder_app/purchase_request_list')
    else:
        form = PurchaseRequestForm(instance=pr)

    return render(request, 'reorder_app/purchase_request_update.html', {
        'form': form,
        'pr': pr
    })


# @login_required
def purchase_request_delete(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    pr.delete()
    messages.success(request, 'Purchase request deleted')
    return redirect('reorder_app/purchase_request_list')


# ==================== Purchase Order ====================

# # @login_required
# def purchase_order_list(request):
#     """List all purchase orders"""
#     pos = PurchaseOrder.objects.select_related(
#         'product', 'supplier', 'created_by'
#     ).order_by('-created_at')
    
#     # Apply filters
#     filter_form = PurchaseOrderFilterForm(request.GET)
#     if filter_form.is_valid():
#         if filter_form.cleaned_data.get('status'):
#             pos = pos.filter(status=filter_form.cleaned_data['status'])
#         if filter_form.cleaned_data.get('product'):
#             pos = pos.filter(product=filter_form.cleaned_data['product'])
#         if filter_form.cleaned_data.get('supplier'):
#             pos = pos.filter(supplier=filter_form.cleaned_data['supplier'])
#         if filter_form.cleaned_data.get('date_from'):
#             pos = pos.filter(created_at__gte=filter_form.cleaned_data['date_from'])
#         if filter_form.cleaned_data.get('date_to'):
#             pos = pos.filter(created_at__lte=filter_form.cleaned_data['date_to'])
    
#     paginator = Paginator(pos, 20)
#     page = request.GET.get('page')
#     pos_page = paginator.get_page(page)
    
#     return render(request, 'reorder_app/purchase_order_list.html', {
#         'pos': pos_page,
#         'filter_form': filter_form
#     })


# # @login_required
# def purchase_order_create(request):
#     """Create purchase order"""
#     if request.method == 'POST':
#         form = PurchaseOrderForm(request.POST, user=request.user)
#         if form.is_valid():
#             po = form.save()
#             # Update purchase request status if linked
#             if po.purchase_request:
#                 po.purchase_request.status = 'CONVERTED'
#                 po.purchase_request.save()
#             messages.success(request, f'Purchase order {po.po_number} created successfully!')
#             return redirect('purchase_order_list')
#     else:
#         form = PurchaseOrderForm()
    
#     return render(request, 'reorder_app/purchase_order_form.html', {'form': form})


# # @login_required
# def pending_po_tracker(request):
#     """Track pending purchase orders"""
#     pending_pos = PurchaseOrder.objects.filter(
#         status__in=['DRAFT', 'SENT', 'CONFIRMED', 'PARTIAL']
#     ).select_related('product', 'supplier').order_by('expected_delivery_date')
    
#     return render(request, 'reorder_app/pending_po_tracker.html', {'pending_pos': pending_pos})

# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.utils import timezone
# from decimal import Decimal

# from .models import PurchaseOrder, Product, Supplier, PurchaseRequest


# # @login_required
# def purchase_order_list(request):
#     orders = PurchaseOrder.objects.select_related(
#         'product', 'supplier', 'purchase_request'
#     )
#     return render(request, 'reorder_app/purchase_order_list.html', {
#         'orders': orders
#     })


# # @login_required
# def purchase_order_create(request):
#     products = Product.objects.all()
#     suppliers = Supplier.objects.all()
#     purchase_requests = PurchaseRequest.objects.filter(status='APPROVED')

#     if request.method == 'POST':
#         po = PurchaseOrder.objects.create(
#             purchase_request_id=request.POST.get('purchase_request') or None,
#             product_id=request.POST['product'],
#             supplier_id=request.POST['supplier'],
#             quantity=int(request.POST['quantity']),
#             unit_price=Decimal(request.POST['unit_price']),
#             expected_delivery_date=request.POST['expected_delivery_date'],
#             status=request.POST.get('status', 'DRAFT'),
#             created_by=request.user,
#             notes=request.POST.get('notes', '')
#         )
#         return redirect('purchase_order_list')

#     return render(request, 'reorder_app/purchase_order_form.html', {
#         'products': products,
#         'suppliers': suppliers,
#         'purchase_requests': purchase_requests
#     })


# # @login_required
# def purchase_order_update(request, pk):
#     po = get_object_or_404(PurchaseOrder, pk=pk)
#     products = Product.objects.all()
#     suppliers = Supplier.objects.all()
#     purchase_requests = PurchaseRequest.objects.filter(status='APPROVED')

#     if request.method == 'POST':
#         po.purchase_request_id = request.POST.get('purchase_request') or None
#         po.product_id = request.POST['product']
#         po.supplier_id = request.POST['supplier']
#         po.quantity = int(request.POST['quantity'])
#         po.unit_price = Decimal(request.POST['unit_price'])
#         po.status = request.POST['status']
#         po.expected_delivery_date = request.POST['expected_delivery_date']
#         po.actual_delivery_date = request.POST.get('actual_delivery_date') or None
#         po.notes = request.POST.get('notes', '')
#         po.save()
#         return redirect('purchase_order_list')

#     return render(request, 'reorder_app/purchase_order_form.html', {
#         'po': po,
#         'products': products,
#         'suppliers': suppliers,
#         'purchase_requests': purchase_requests
#     })


# # @login_required
# def pending_po_tracker(request):
#     orders = PurchaseOrder.objects.filter(
#         status__in=['DRAFT', 'SENT', 'CONFIRMED', 'PARTIAL']
#     )
#     return render(request, 'reorder_app/pending_po_tracker.html', {
#         'orders': orders
#     })


# from django.shortcuts import render, redirect
# from .forms import PurchaseOrderForm, PurchaseOrderLine
# from django.shortcuts import render
# from .models import PurchaseOrder

# def create_purchase_order(request):
#     if request.method == "POST":
#         form = PurchaseOrderForm(request.POST)
#         formset = PurchaseOrderLineFormSet(request.POST)

#         if form.is_valid() and formset.is_valid():
#             order = form.save(commit=False)
#             order.created_by = request.user
#             order.save()

#             formset.instance = order
#             formset.save()

#             return redirect("purchase_order_list")
#     else:
#         form = PurchaseOrderForm()
#         formset = PurchaseOrderLineFormSet()

#     return render(
#         request,
#         "reorder_app/purchase_order_form.html",
#         {
#             "form": form,
#             "formset": formset
#         }
#     )


# def purchase_order_list(request):
#     orders = PurchaseOrder.objects.all().select_related('product', 'supplier')
#     return render(request, "reorder_app/purchase_order_list.html", {"orders": orders})


from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import PurchaseOrderForm,PurchaseOrderLineFormSet
from .models import PurchaseOrderLine, Product

from django.forms import inlineformset_factory
from django.shortcuts import render, redirect
from .models import PurchaseOrder, PurchaseOrderLine
PurchaseOrderLineFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderLine,
    fields=('product', 'description', 'quantity', 'unit_price'),
    extra=1,          # 🔥 THIS IS CRITICAL
    can_delete=True
)


def purchase_order_create(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        formset = PurchaseOrderLineFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()

            formset.instance = po
            formset.save()

            return redirect('purchase_order_list')
    else:
        form = PurchaseOrderForm()
        formset = PurchaseOrderLineFormSet()

    return render(request, 'reorder_app/purchase_order_form.html', {
        'form': form,
        'formset': formset
    })

@login_required
def purchase_order_list(request):
    pos = (
        PurchaseOrder.objects
        .select_related('supplier', 'created_by')
        .prefetch_related('lines__product')
        .order_by('-order_date')
    )

    filter_form = PurchaseOrderFilterForm(request.GET or None)

    # ✅ Apply filters ONLY when filters are submitted
    if request.GET and filter_form.is_valid():

        status = filter_form.cleaned_data.get('status')
        product = filter_form.cleaned_data.get('product')
        supplier = filter_form.cleaned_data.get('supplier')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')

        if status:
            pos = pos.filter(status=status)

        if supplier:
            pos = pos.filter(supplier=supplier)

        if product:
            pos = pos.filter(lines__product=product)

        if date_from:
            pos = pos.filter(order_date__date__gte=date_from)

        if date_to:
            pos = pos.filter(order_date__date__lte=date_to)

        pos = pos.distinct()

    paginator = Paginator(pos, 1000)
    page = request.GET.get('page')
    pos_page = paginator.get_page(page)

    return render(request, 'reorder_app/purchase_order_list.html', {
        'pos': pos_page,
        'filter_form': filter_form
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import PurchaseOrder
from .forms import PurchaseOrderForm, PurchaseOrderLineFormSet


@login_required
def purchase_order_update(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method == "POST":
        form = PurchaseOrderForm(request.POST, instance=po)
        formset = PurchaseOrderLineFormSet(request.POST, instance=po)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('purchase_order_list')

    else:
        form = PurchaseOrderForm(instance=po)
        formset = PurchaseOrderLineFormSet(instance=po)

    return render(request, 'reorder_app/purchase_order_form.html', {
        'form': form,
        'formset': formset,
        'is_edit': True,   # optional flag for template
        'po': po
    })


from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PurchaseOrder


@login_required
def purchase_order_delete(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method == "POST":
        po.delete()
        messages.success(request, "Purchase Order deleted successfully.")
        return redirect('purchase_order_list')

    # safety fallback (should not normally hit)
    return redirect('purchase_order_list')

def edit_po(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po)
        formset = PurchaseOrderLineFormSet(
            request.POST,
            instance=po        # 🔥 THIS IS CRITICAL
        )

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()     # 🔥 THIS IS WHAT UPDATES LINES
            return redirect('purchase_order_list')

    else:
        form = PurchaseOrderForm(instance=po)
        formset = PurchaseOrderLineFormSet(instance=po)

    return render(request, 'reorder_app/purchase_order_form.html', {
        'form': form,
        'formset': formset,
        'po': po,
        'is_edit': True
    })


# ==================== Stock Movement ====================

# @login_required
def stock_movement_create(request):
    """Create stock movement"""
    if request.method == 'POST':
        form = StockMovementForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stock movement recorded successfully!')
            return redirect('dashboard')
    else:
        form = StockMovementForm()
    
    return render(request, 'reorder_app/stock_movement_form.html', {'form': form})

   
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import StockMovement, Product, PurchaseOrder




@login_required
def stock_movement_create(request):
    products = Product.objects.all()
    purchase_orders = PurchaseOrder.objects.all()

    if request.method == 'POST':
        StockMovement.objects.create(
            product_id=request.POST['product'],
            movement_type=request.POST['movement_type'],
            quantity=int(request.POST['quantity']),
            reference_number=request.POST.get('reference_number', ''),
            purchase_order_id=request.POST.get('purchase_order') or None,
            notes=request.POST.get('notes', ''),
            performed_by=request.user
        )
        return redirect('stock_movement_list')

    return render(request, 'reorder_app/stock_movement_form.html', {
        'products': products,
        'purchase_orders': purchase_orders
    })


@login_required
def stock_movement_update(request, pk):
    movement = get_object_or_404(StockMovement, pk=pk)
    products = Product.objects.all()
    purchase_orders = PurchaseOrder.objects.all()

    if request.method == 'POST':
        movement.product_id = request.POST['product']
        movement.movement_type = request.POST['movement_type']
        movement.quantity = int(request.POST['quantity'])
        movement.reference_number = request.POST.get('reference_number', '')
        movement.purchase_order_id = request.POST.get('purchase_order') or None
        movement.notes = request.POST.get('notes', '')
        movement.save()
        return redirect('stock_movement_list')

    return render(request, 'reorder_app//stock_movement_form.html', {
        'movement': movement,
        'products': products,
        'purchase_orders': purchase_orders
    })


# ==================== Export Functions ====================

# @login_required
def export_purchase_orders(request):
    """Export purchase orders to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="purchase_orders.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['PO Number', 'Product', 'Supplier', 'Quantity', 'Unit Price', 
                     'Total Value', 'Status', 'Expected Delivery', 'Created At'])
    
    pos = PurchaseOrder.objects.select_related('product', 'supplier').all()
    for po in pos:
        writer.writerow([
            po.po_number, po.product.name, po.supplier.name, po.quantity,
            po.unit_price, po.total_value, po.get_status_display(),
            po.expected_delivery_date, po.created_at.strftime('%Y-%m-%d')
        ])
    
    return response


# @login_required
def export_purchase_requests(request):
    """Export purchase requests to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="purchase_requests.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Request Number', 'Product', 'Supplier', 'Quantity', 
                     'Unit Price', 'Total Value', 'Priority', 'Status', 'Requested Date'])
    
    prs = PurchaseRequest.objects.select_related('product', 'supplier').all()
    for pr in prs:
        writer.writerow([
            pr.request_number, pr.product.name, pr.supplier.name, pr.quantity,
            pr.unit_price, pr.total_value, pr.get_priority_display(),
            pr.get_status_display(), pr.requested_date.strftime('%Y-%m-%d')
        ])
    
    return response


# ==================== AJAX/API Views ====================

# @login_required
def get_product_details(request, pk):
    """Get product details as JSON"""
    product = get_object_or_404(Product, pk=pk)
    data = {
        'id': product.id,
        'name': product.name,
        'sku': product.sku,
        'current_stock': product.current_stock,
        'reorder_point': product.reorder_point,
        'unit_price': str(product.unit_price),
        'needs_reorder': product.needs_reorder(),
    }
    return JsonResponse(data)


# @login_required
def get_supplier_products(request, pk):
    """Get products for a supplier"""
    mappings = ProductSupplierMapping.objects.filter(
        supplier_id=pk, is_active=True
    ).select_related('product')
    
    products = [{
        'id': m.product.id,
        'name': m.product.name,
        'unit_price': str(m.unit_price),
        'lead_time': m.lead_time_days,
    } for m in mappings]
    
    return JsonResponse({'products': products})

from django.shortcuts import render, redirect
from django.forms import modelformset_factory
from django.utils import timezone
from .models import SalesOrder, SalesOrderItem
from .forms import SalesOrderForm, SalesOrderItemForm

def create_sales_order(request):
    SalesOrderItemFormSet = modelformset_factory(
        SalesOrderItem,
        form=SalesOrderItemForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        form = SalesOrderForm(request.POST)
        formset = SalesOrderItemFormSet(
            request.POST,
            queryset=SalesOrderItem.objects.none(),
            prefix='lines'
        )

        if form.is_valid() and formset.is_valid():
            sales_order = form.save()

            for f in formset.cleaned_data:
                if f and not f.get('DELETE', False):
                    SalesOrderItem.objects.create(
                        sales_order=sales_order,
                        product=f['product'],
                        description=f['description'],
                        quantity=f['quantity'],
                        unit_price=f['unit_price'],
                        subtotal=f['quantity'] * f['unit_price']
                    )

            return redirect('sales_order_list')

    else:
        form = SalesOrderForm(initial={'order_date': timezone.now()})
        formset = SalesOrderItemFormSet(
            queryset=SalesOrderItem.objects.none(),
            prefix='lines'
        )

    return render(request, 'reorder_app/sales_order_form.html', {
        'form': form,
        'formset': formset
    })


def sales_order_list(request):
    orders = SalesOrder.objects.prefetch_related('items', 'items__product')

    for order in orders:
        order.total_qty = sum(item.quantity for item in order.items.all())
        order.total_value = sum(item.subtotal for item in order.items.all())

    return render(request, 'reorder_app/sales_order_list.html', {
        'orders': orders
    })


def sales_order_update(request, pk):
    sales_order = get_object_or_404(SalesOrder, pk=pk)

    SalesOrderItemFormSet = modelformset_factory(
        SalesOrderItem,
        form=SalesOrderItemForm,
        extra=0,
        can_delete=True
    )

    if request.method == 'POST':
        form = SalesOrderForm(request.POST, instance=sales_order)
        formset = SalesOrderItemFormSet(
            request.POST,
            queryset=sales_order.items.all(),
            prefix='lines'
        )

        if form.is_valid() and formset.is_valid():
            form.save()

            for f in formset:
                if f.cleaned_data:
                    if f.cleaned_data.get('DELETE'):
                        if f.instance.pk:
                            f.instance.delete()
                    else:
                        obj = f.save(commit=False)
                        obj.sales_order = sales_order
                        obj.subtotal = obj.quantity * obj.unit_price
                        obj.save()

            return redirect('sales_order_list')

    else:
        form = SalesOrderForm(instance=sales_order)
        formset = SalesOrderItemFormSet(
            queryset=sales_order.items.all(),
            prefix='lines'
        )

    return render(request, 'reorder_app/sales_order_form.html', {
        'form': form,
        'formset': formset,
        'is_update': True
    })


def sales_order_delete(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)
    order.delete()
    return redirect('sales_order_list')


from django.http import JsonResponse
from reorder_app.service import get_ai_inventory_decision


def ai_inventory_decision_view(request):
    """
    API endpoint for AI inventory decision
    """

    item_id = 1
    month = "March 2026"

    result = get_ai_inventory_decision(
        item_id=item_id,
        month=month
    )

    return JsonResponse(result)
