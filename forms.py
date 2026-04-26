from django import forms 
from django.contrib.auth.forms import UserCreationForm
from .models import (
    Product, Supplier, ProductSupplierMapping, 
    PurchaseRequest, PurchaseOrder, ConsumptionReport,
    ReorderRule, StockMovement,Reorder,Consumer
)

# reorder_app/forms.py
from django.contrib.auth.models import User

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_staff = True   # ⭐ so user can see admin tables
        if commit:
            user.save()
        return user

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'sku',
            'category',
            'description',
            'unit_of_measure',
            "unit_price",
            'is_active',
        ]

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter SKU / Barcode'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Product description'
            }),
            'unit_of_measure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. kg, liters, packets'
            }),
            "unit_price": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "placeholder": "Unit price"
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class SupplierForm(forms.ModelForm):
    """Form for Supplier Creation / Update"""

    class Meta:
        model = Supplier
        fields = [
            'supplier_code',
            'name',
            'email',
            'phone',
            'address',
            'is_active',
        ]

        widgets = {
            'supplier_code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'SUP-001',
                'maxlength': 50,
            }),

            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Supplier Name',
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'email@example.com',
            }),

            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+91 9876543210',
            }),

            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Full Address',
            }),

            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }


class ProductSupplierMappingForm(forms.ModelForm):
    """Form for Product-Supplier Mapping"""
    class Meta:
        model = ProductSupplierMapping
        fields = [
            'product', 'supplier', 'lead_time_days', 
            'supplier_sku', 'unit_price', 'minimum_order_quantity',
            'is_preferred', 'is_active'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'lead_time_days': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Days'}),
            'supplier_sku': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Supplier SKU'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00', 'step': '0.01'}),
            'minimum_order_quantity': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '1'}),
            'is_preferred': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class ConsumptionReportForm(forms.ModelForm):
    """Form for Consumption Report"""
    class Meta:
        model = ConsumptionReport
        fields = [
            'product', 'period_type', 'start_date', 
            'end_date', 'quantity_consumed', 'average_daily_consumption', 'notes'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'period_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'quantity_consumed': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0'}),
            'average_daily_consumption': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Additional notes'}),
        }
class ConsumerForm(forms.ModelForm):
    class Meta:
        model = Consumer
        fields = ['pro_name', 'consumed_date', 'consumer_quantity']
        widgets = {
            'consumed_date': forms.DateInput(attrs={'type': 'date'}),
            'consumer_quantity': forms.NumberInput(attrs={'min': 0}),
        }


class ReorderRuleForm(forms.ModelForm):
    """Form for Reorder Rules"""
    class Meta:
        model = ReorderRule
        fields = [
            'product', 'eoq_quantity', 'safety_stock', 
            'predicted_reorder_date', 'priority', 'ml_confidence_score', 'is_active'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'eoq_quantity': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'EOQ Quantity'}),
            'safety_stock': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Safety Stock'}),
            'predicted_reorder_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'ml_confidence_score': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

class ReorderForm(forms.ModelForm):
    class Meta:
        model = Reorder
        fields = ['product', 'min_qty', 'max_qty', 'reorder_qty']
        widgets = {
            'min_qty': forms.NumberInput(attrs={'min': 0}),
            'max_qty': forms.NumberInput(attrs={'min': 0}),
            'reorder_qty': forms.NumberInput(attrs={'min': 0}),
        }

class PurchaseRequestForm(forms.ModelForm):
    """Form for Purchase Request"""
    class Meta:
        model = PurchaseRequest
        fields = ['product', 'supplier', 'quantity', 'unit_price', 'priority', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Quantity'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00', 'step': '0.01'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Additional notes'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.requested_by = self.user
        if commit:
            instance.save()
        return instance


# class PurchaseOrderForm(forms.ModelForm):
#     """Form for Purchase Order"""
#     class Meta:
#         model = PurchaseOrder
#         fields = [
#             'purchase_request', 'product', 'supplier', 
#             'quantity', 'unit_price', 'expected_delivery_date', 
#             'status', 'notes'
#         ]
#         widgets = {
#             'purchase_request': forms.Select(attrs={'class': 'form-select'}),
#             'product': forms.Select(attrs={'class': 'form-select'}),
#             'supplier': forms.Select(attrs={'class': 'form-select'}),
#             'quantity': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Quantity'}),
#             'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00', 'step': '0.01'}),
#             'expected_delivery_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
#             'status': forms.Select(attrs={'class': 'form-select'}),
#             'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Additional notes'}),
#         }

#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)

#     def save(self, commit=True):
#         instance = super().save(commit=False)
#         if self.user:
#             instance.created_by = self.user
#         if commit:
#             instance.save()
#         return instance

from django import forms
from django.forms import inlineformset_factory
from .models import PurchaseOrder, PurchaseOrderLine


# forms.py
class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ["supplier", "order_date", "status", "notes"]
        widgets = {
            "order_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class PurchaseOrderLineForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderLine
        fields = ["product", "description", "quantity", "unit_price"]


PurchaseOrderLineFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderLine,
    form=PurchaseOrderLineForm,
    extra=1,
    can_delete=True
)



# from django import forms
# from .models import PurchaseOrder

# class PurchaseOrderForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         self.user = kwargs.pop('user', None)  # ✅ remove user safely
#         super().__init__(*args, **kwargs)

#         Example usage (optional)
#         if self.user:
#             self.fields['supplier'].queryset = Supplier.objects.filter(user=self.user)

#     class Meta:
#         model = PurchaseOrder
#         fields = '__all__'


class StockMovementForm(forms.ModelForm):
    """Form for Stock Movement"""
    class Meta:
        model = StockMovement
        fields = [
            'product', 'movement_type', 'quantity', 
            'reference_number', 'purchase_order', 'notes'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Quantity'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Reference Number'}),
            'purchase_order': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Additional notes'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.performed_by = self.user
        if commit:
            instance.save()
        return instance



class PurchaseRequestFilterForm(forms.Form):
    """Filter form for Purchase Requests"""
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(PurchaseRequest.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + list(ReorderRule.PRIORITY_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )


class PurchaseOrderFilterForm(forms.Form):
    """Filter form for Purchase Orders"""
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(PurchaseOrder.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )


from django import forms
from .models import SalesOrder, SalesOrderItem

class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = ['customer', 'order_date']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'order_date': forms.DateTimeInput(
                attrs={"type": "date"}
            ),
        }


class SalesOrderItemForm(forms.ModelForm):
    class Meta:
        model = SalesOrderItem
        fields = ['product', 'description', 'quantity', 'unit_price', 'subtotal']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
from django import forms
from .models import PurchaseOrder, Supplier


class PurchaseOrderFilterForm(forms.Form):
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        required=False,
        empty_label="All Suppliers"
    )

    status = forms.ChoiceField(
        choices=[("", "All Statuses")] + list(PurchaseOrder.STATUS_CHOICES),
        required=False
    )
