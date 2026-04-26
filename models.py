from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class Supplier(models.Model):
    """Supplier Master Data"""

    supplier_code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text="Internal supplier reference code"
    )

    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'suppliers'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.supplier_code})"


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('FRU', 'Fruits & Vegetables'),
        ('DAI', 'Dairy & Eggs'),
        ('BEV', 'Beverages'),
        ('SNK', 'Snacks & Confectionery'),
        ('BKR', 'Bakery & Bread'),
        ('HBC', 'Health & Beauty Care'),
        ('HHC', 'Household Care'),
        ('FRO', 'Frozen Foods'),
        ('MEA', 'Meat & Seafood'),
        ('GRA', 'Grains, Pulses & Pasta'),
        ('OIL', 'Oils & Condiments'),
    ]
    product_id = models.CharField(max_length=10, unique=True,null=True, blank=True)
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=3, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    unit_of_measure = models.CharField(max_length=50, default='units')
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"


class ProductSupplierMapping(models.Model):
    """Product-Supplier Mapping with Lead Time"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='suppliers')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    lead_time_days = models.IntegerField(help_text="Lead time in days")
    supplier_sku = models.CharField(max_length=100, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_quantity = models.IntegerField(default=1)
    is_preferred = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_supplier_mapping'
        unique_together = ['product', 'supplier']
        ordering = ['product', '-is_preferred']

    def __str__(self):
        return f"{self.product.name} - {self.supplier.name}"


class ConsumptionReport(models.Model):
    """Daily/Weekly/Monthly Consumption Tracking"""
    PERIOD_CHOICES = [
        ('D', 'Daily'),
        ('W', 'Weekly'),
        ('M', 'Monthly'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='consumption_reports')
    period_type = models.CharField(max_length=1, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    quantity_consumed = models.IntegerField()
    average_daily_consumption = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'consumption_reports'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.product.name} - {self.start_date} to {self.end_date}"
    

class Consumer(models.Model):
    pro_name = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    consumed_date = models.DateField(default=timezone.now)
    consumer_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.pro_name)



class ReorderRule(models.Model):
    """AI-Powered Reorder Rules"""
    PRIORITY_CHOICES = [
        ('H', 'High'),
        ('M', 'Medium'),
        ('L', 'Low'),
    ]

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='reorder_rule')
    eoq_quantity = models.IntegerField(help_text="Economic Order Quantity")
    safety_stock = models.IntegerField(default=0)
    predicted_reorder_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default='M')
    ml_confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    rule_parameters = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reorder_rules'

    def __str__(self):
        return f"Reorder Rule for {self.product.name}"

class Reorder(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    min_qty = models.PositiveIntegerField(default=0)
    max_qty = models.PositiveIntegerField(default=0)
    reorder_qty = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.product)


class PurchaseRequest(models.Model):
    """Purchase Request List"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CONVERTED', 'Converted to PO'),
    ]

    request_number = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=12, decimal_places=2)
    priority = models.CharField(max_length=1, choices=ReorderRule.PRIORITY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='purchase_requests')
    requested_date = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approved_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    ai_generated = models.BooleanField(default=False)

    class Meta:
        db_table = 'purchase_requests'
        ordering = ['-requested_date']

    def __str__(self):
        return f"{self.request_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            # Auto-generate request number
            last_req = PurchaseRequest.objects.all().order_by('-id').first()
            if last_req:
                num = int(last_req.request_number.split('-')[-1]) + 1
            else:
                num = 1
            self.request_number = f"PR-{timezone.now().year}-{num:04d}"
        
        self.total_value = Decimal(self.quantity) * self.unit_price
        super().save(*args, **kwargs)


# class PurchaseOrder(models.Model):
#     """Purchase Order (PO) Management"""
#     STATUS_CHOICES = [
#         ('DRAFT', 'Draft'),
#         ('SENT', 'Sent to Supplier'),
#         ('CONFIRMED', 'Confirmed by Supplier'),
#         ('PARTIAL', 'Partially Received'),
#         ('RECEIVED', 'Fully Received'),
#         ('CANCELLED', 'Cancelled'),
#     ]

#     po_number = models.CharField(max_length=50, unique=True)
#     purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.SET_NULL, null=True, blank=True)
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
#     quantity = models.IntegerField()
#     unit_price = models.DecimalField(max_digits=10, decimal_places=2)
#     total_value = models.DecimalField(max_digits=12, decimal_places=2)
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
#     expected_delivery_date = models.DateField()
#     actual_delivery_date = models.DateField(null=True, blank=True)
#     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     notes = models.TextField(blank=True)

#     class Meta:
#         db_table = 'purchase_orders'
#         ordering = ['-created_at']

#     def __str__(self):
#         return f"{self.po_number} - {self.product.name}"

#     def save(self, *args, **kwargs):
#         if not self.po_number:
#             # Auto-generate PO number
#             last_po = PurchaseOrder.objects.all().order_by('-id').first()
#             if last_po:
#                 num = int(last_po.po_number.split('-')[-1]) + 1
#             else:
#                 num = 1
#             self.po_number = f"PO-{timezone.now().year}-{num:04d}"
        
#         self.total_value = Decimal(self.quantity) * self.unit_price
#         super().save(*args, **kwargs)

#     def is_pending(self):
#         return self.status in ['DRAFT', 'SENT', 'CONFIRMED', 'PARTIAL']



from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('CONFIRMED', 'Confirmed'),
    ]

    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE)
    order_date = models.DateTimeField(default=timezone.now)
    vendor_reference = models.CharField(max_length=100, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def total_amount(self):
        return sum(line.subtotal() for line in self.lines.all())

    def __str__(self):
        return f"PO-{self.id}"


class PurchaseOrderLine(models.Model):
    order = models.ForeignKey(
        PurchaseOrder,
        related_name="lines",
        on_delete=models.CASCADE
    )
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantity * self.unit_price
    
from .models import PurchaseOrder


from django.db import models
from django.utils import timezone


class StockMovement(models.Model):
    """Track Stock In/Out Movements"""
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJ', 'Adjustment'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=3, choices=MOVEMENT_TYPES,null=True)
    quantity = models.IntegerField(null=True)
    reference_number = models.CharField(max_length=100, blank=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

    class Meta:
        db_table = 'stock_movements'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.movement_type} - {self.product.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product stock
        if self.movement_type == 'IN':
            self.product.current_stock += self.quantity
        elif self.movement_type == 'OUT':
            self.product.current_stock -= self.quantity
        elif self.movement_type == 'ADJ':
            self.product.current_stock = self.quantity
        self.product.save()


class MLPrediction(models.Model):
    """Store ML Predictions for Analysis"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    prediction_date = models.DateField(auto_now_add=True)
    predicted_demand = models.IntegerField()
    predicted_reorder_date = models.DateField()
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)
    model_version = models.CharField(max_length=50)
    features_used = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ml_predictions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Prediction for {self.product.name} on {self.prediction_date}"
    


from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class SalesOrder(models.Model):
    so_number = models.CharField(max_length=20,null=True, blank=True,unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order_date = models.DateField()

    class Meta:
        ordering = ['-order_date']  # 👈 DESCENDING

    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())

    def __str__(self):
        return f"SO-{self.id}"


class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(
        SalesOrder,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product} - {self.sales_order}"

    