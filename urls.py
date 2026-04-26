from django.urls import path
from . import views
from .views import ai_inventory_decision_view 

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/',views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),

       # Product Management
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/update/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('api/products/<int:pk>/', views.get_product_details, name='get_product_details'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/edit/<int:id>/', views.product_edit, name='product_edit'),
    path('products/delete/<int:id>/', views.product_delete, name='product_delete'),

    # Supplier Management
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/update/', views.supplier_update, name='supplier_update'),
    path('api/suppliers/<int:pk>/products/', views.get_supplier_products, name='get_supplier_products'),
    # urls.py
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.add_supplier, name='add_supplier'),
    path('suppliers/update/<int:pk>/', views.update_supplier, name='update_supplier'),
    path('suppliers/delete/<int:pk>/', views.delete_supplier, name='delete_supplier'),

    # Product-Supplier Mapping
    path('mappings/', views.mapping_list, name='mapping_list'),
    path('mappings/create/', views.mapping_create, name='mapping_create'),
    path('product-supplier/', views.product_supplier_list, name='product_supplier_list'),
    path('product-supplier/add/',views. add_product_supplier, name='add_product_supplier'),
    path('product-supplier/update/<int:pk>/',views. update_product_supplier, name='update_product_supplier'),
    path('product-supplier/delete/<int:pk>/', views.delete_product_supplier, name='delete_product_supplier'),

    # Consumption Report
    path('consumption-reports/', views.consumption_report_list, name='consumption_report_list'),
    path('consumption-reports/create/', views.consumption_report_create, name='consumption_report_create'),
    path('conslst',views.consumerlst,name='consumer'),
    path('consform', views.consuform, name='consuform'),
    path('conup/<int:id>/', views.consumerup, name='update'),  
    path('condl/<int:id>/', views.consdl, name='delete'),  
    path("report/", views.consumption_report, name="report"),
    # Reorder Rule Engine
    path('reorder-rules/', views.reorder_rule_list, name='reorder_rule_list'),
    path('reorder-rules/create/', views.reorder_rule_create, name='reorder_rule_create'),
    path('reorderlist',views.reorderlist,name='reorder'),
    path('reform', views.reform, name='reform'),
    path('reup/<int:id>/', views.reup, name='reupdate'),  
    path('redl/<int:id>/', views.redl, name='redelete'), 
    
    # Purchase Request
    path('purchase-requests/', views.purchase_request_list, name='purchase_request_list'),
    path('purchase-requests/create/', views.purchase_request_create, name='purchase_request_create'),
    path('purchase-requests/<int:pk>/approve/', views.purchase_request_approve, name='purchase_request_approve'),
    path('purchase-requests/',views. purchase_request_list, name='purchase_request_list'),
    path('purchase-requests/create/', views.purchase_request_create, name='purchase_request_create'),
    path('purchase-requests/update/<int:pk>/',views. purchase_request_update, name='purchase_request_update'),
    path('purchase-requests/delete/<int:pk>/',views. purchase_request_delete, name='purchase_request_delete'),

    # Purchase Order
    # path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    # path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
    # path('purchase-orders/pending/', views.pending_po_tracker, name='pending_po_tracker'),
    # path('purchase-orders/',views. purchase_order_list, name='purchase_order_list'),
    # path('purchase-orders/create/',views. purchase_order_create, name='purchase_order_create'),
    # path('purchase-orders/update/<int:pk>/',views. purchase_order_update, name='purchase_order_update'),
    # path('purchase-orders/pending/',views. pending_po_tracker, name='pending_po_tracker'),
    path('purchase-orders/',views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-orders/<int:pk>/edit/',views.purchase_order_update,name='purchase_order_update'),
    path('purchase-orders/<int:pk>/delete/',views.purchase_order_delete,name='purchase_order_delete'),
    path('sales-orders/create/', views.create_sales_order, name='sales_order_create'),
    path('sales-orders/', views.sales_order_list, name='sales_order_list'),
    path('sales-orders/<int:pk>/edit/', views.sales_order_update, name='sales_order_update'),
    path('sales-orders/<int:pk>/delete/', views.sales_order_delete, name='sales_order_delete'),

    # Stock Movement
    path('stock-movements/create/', views.stock_movement_create, name='stock_movement_create'),
    path('stock-movements/create/', views.stock_movement_create, name='stock_movement_create'),
    path('stock-movements/update/<int:pk>/',views. stock_movement_update, name='stock_movement_update'),

    # Export Functions
    path('export/purchase-orders/', views.export_purchase_orders, name='export_purchase_orders'),
    path('export/purchase-requests/', views.export_purchase_requests, name='export_purchase_requests'),
    path("ai-decision/", ai_inventory_decision_view, name="ai-decision"),



]
