from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

urlpatterns = [
    # Authentication
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Password reset
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # User management
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # Category management
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    
    # Product management
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Product variant management
    path('product-variants/', views.ProductVariantListView.as_view(), name='product-variant-list'),
    path('product-variants/<int:pk>/', views.ProductVariantDetailView.as_view(), name='product-variant-detail'),
    
    # Warehouse management
    path('warehouses/', views.WarehouseListView.as_view(), name='warehouse-list'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse-detail'),
    
    # Inventory management
    path('inventory/', views.InventoryListView.as_view(), name='inventory-list'),
    path('inventory/<int:pk>/', views.InventoryDetailView.as_view(), name='inventory-detail'),
    
    # Customer management
    path('customers/', views.CustomerListView.as_view(), name='customer-list'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer-detail'),
    
    # Sales
    path('sales/', views.SaleListView.as_view(), name='sale-list'),
    path('sales/<int:pk>/', views.SaleDetailView.as_view(), name='sale-detail'),
    
    # Transfers
    path('transfers/', views.TransferListView.as_view(), name='transfer-list'),
    path('transfers/<int:pk>/', views.TransferDetailView.as_view(), name='transfer-detail'),
    
    # Audit logs
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit-log-list'),
    
    # POS Sales
    path('sales/create/', views.create_sale, name='create-sale'),
    
    # Receipt
    path('sales/<int:pk>/receipt/', views.get_receipt, name='get-receipt'),
    
    # Customer purchase history
    path('customers/<int:pk>/purchase-history/', views.customer_purchase_history, name='customer-purchase-history'),
    
    # Low stock alerts
    path('inventory/low-stock/', views.low_stock_alerts, name='low-stock-alerts'),
    
    # Purchase Orders & Receiving
    path('purchase-orders/', views.PurchaseOrderListView.as_view(), name='purchase-order-list'),
    path('purchase-orders/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='purchase-order-detail'),
    path('grns/', views.GoodsReceivedNoteListView.as_view(), name='grn-list'),
    path('grns/<int:pk>/', views.GoodsReceivedNoteDetailView.as_view(), name='grn-detail'),
    
    # Promotions/Discounts
    path('promotions/', views.PromotionListView.as_view(), name='promotion-list'),
    path('promotions/<int:pk>/', views.PromotionDetailView.as_view(), name='promotion-detail'),
    path('coupons/', views.CouponListView.as_view(), name='coupon-list'),
    path('coupons/<int:pk>/', views.CouponDetailView.as_view(), name='coupon-detail'),
    
    # Returns/Exchanges
    path('returns/', views.ReturnListView.as_view(), name='return-list'),
    path('returns/<int:pk>/', views.ReturnDetailView.as_view(), name='return-detail'),
    
    # Reports
    path('reports/sales/', views.sales_report, name='sales-report'),
    path('reports/inventory/', views.inventory_report, name='inventory-report'),
    path('reports/profitability/', views.profitability_report, name='profitability-report'),
    path('reports/transfers/', views.transfer_report, name='transfer-report'),
    
    # Super Admin User Management
    path('super-admin/users/', views.SuperAdminUserManagementView.as_view(), name='super-admin-user-list'),
    path('super-admin/users/<int:pk>/', views.SuperAdminUserDetailView.as_view(), name='super-admin-user-detail'),
    path('super-admin/users/<int:pk>/reset-password/', views.reset_user_password, name='reset-user-password'),
    path('user-management-dashboard/', views.user_management_dashboard, name='user-management-dashboard'),
]