from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, mfa_views

# Create router and register ViewSets
router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'warehouses', views.WarehouseViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'bins', views.BinViewSet)
router.register(r'customers', views.CustomerViewSet)
router.register(r'sales', views.SaleViewSet)
router.register(r'inventory', views.InventoryViewSet)
router.register(r'transfers', views.TransferViewSet)
router.register(r'product-variants', views.ProductVariantViewSet)
router.register(r'webhooks', views.WebhookViewSet)
router.register(r'webhook-logs', views.WebhookLogViewSet)
router.register(r'payment-tokens', views.PaymentTokenViewSet)
router.register(r'payment-gateway-configs', views.PaymentGatewayConfigViewSet)
router.register(r'ecommerce-platforms', views.EcommercePlatformViewSet)
router.register(r'ecommerce-sync-logs', views.EcommerceSyncLogViewSet)
router.register(r'reservations', views.ReservationViewSet, basename='reservation')

urlpatterns = [
    # Include the router URLs for ViewSets
    path('', include(router.urls)),
    # Authentication
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Password reset
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset-validate/<uidb64>/<token>/', views.password_reset_validate_token, name='password_reset_validate_token'),
    
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
    
    # Customer loyalty points
    path('customers/<int:customer_id>/earn-points/', views.earn_loyalty_points, name='earn-loyalty-points'),
    path('customers/<int:customer_id>/redeem-points/', views.redeem_loyalty_points, name='redeem-loyalty-points'),
    path('customers/apply-loyalty-discount/', views.apply_loyalty_discount, name='apply-loyalty-discount'),
    
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
    path('sales/<int:pk>/email-receipt/', views.email_receipt, name='email-receipt'),
    path('sales/<int:pk>/print-receipt/', views.print_receipt, name='print-receipt'),
    
    # Additional payment to sale (for partial payments)
    path('sales/<int:pk>/add-payment/', views.add_payment_to_sale, name='add-payment-to-sale'),
    
    # Customer purchase history
    path('customers/<int:pk>/purchase-history/', views.customer_purchase_history, name='customer-purchase-history'),
    

    
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
    path('coupons/verify/<str:code>/', views.verify_coupon, name='verify-coupon'),
    
    # Returns/Exchanges
    path('returns/', views.ReturnListView.as_view(), name='return-list'),
    path('returns/<int:pk>/', views.ReturnDetailView.as_view(), name='return-detail'),
    path('returns/lookup-by-receipt/<str:receipt_number>/', views.lookup_returns_by_receipt, name='lookup-returns-by-receipt'),
    path('returns/lookup-by-customer/<int:customer_id>/', views.lookup_returns_by_customer, name='lookup-returns-by-customer'),
    path('returns/<int:return_id>/process/', views.process_return, name='process-return'),
    
    # Reports
    path('reports/sales/', views.sales_report, name='sales-report'),
    path('reports/inventory/', views.inventory_report, name='inventory-report'),
    path('reports/profitability/', views.profitability_report, name='profitability-report'),
    path('reports/transfers/', views.transfer_report, name='transfer-report'),
    
    # Report Exports
    path('reports/sales/export/', views.export_sales_report, name='export-sales-report'),
    path('reports/inventory/export/', views.export_inventory_report, name='export-inventory-report'),
    path('reports/profitability/export/', views.export_profitability_report, name='export-profitability-report'),
    path('reports/transfers/export/', views.export_transfer_report, name='export-transfer-report'),
    
    # Super Admin User Management
    path('super-admin/users/', views.SuperAdminUserManagementView.as_view(), name='super-admin-user-list'),
    path('super-admin/users/<int:pk>/', views.SuperAdminUserDetailView.as_view(), name='super-admin-user-detail'),
    path('super-admin/users/<int:pk>/reset-password/', views.reset_user_password, name='reset-user-password'),
    path('super-admin/users/<int:pk>/role/', views.update_user_role, name='update-user-role'),
    path('super-admin/users/create/', views.create_user_with_role, name='create-user-with-role'),
    path('super-admin/users/<int:user_id>/mfa/reset/', mfa_views.reset_user_mfa, name='reset-user-mfa'),
    path('user-management-dashboard/', views.user_management_dashboard, name='user-management-dashboard'),
    
    # MFA (Multi-Factor Authentication)
    path('mfa/enable/', views.enable_mfa, name='enable-mfa'),
    path('mfa/confirm/', views.confirm_mfa, name='confirm-mfa'),
    path('mfa/disable/', views.disable_mfa, name='disable-mfa'),
    path('mfa/verify/', views.verify_mfa, name='verify-mfa'),
    path('mfa/status/', views.mfa_status, name='mfa-status'),
    
    # Token Management
    path('logout/', views.logout, name='logout'),
    path('token/check-validity/', views.check_token_validity, name='check-token-validity'),
    path('super-admin/users/<int:user_id>/blacklist-tokens/', views.blacklist_user_tokens, name='blacklist-user-tokens'),
    path('super-admin/blacklisted-tokens/', views.blacklisted_tokens_list, name='blacklisted-tokens-list'),
    
    # Product bulk operations
    path('products/bulk/', views.bulk_product_operations, name='bulk-product-operations'),
    
    # Inventory by location
    path('inventory-by-location/', views.inventory_by_location, name='inventory-by-location'),
    
    # Payment Gateway Integration
    path('payments/process-gateway/', views.process_payment_gateway, name='process-payment-gateway'),
    path('payments/create-token/', views.create_customer_payment_token, name='create-customer-payment-token'),
    
    # E-commerce Sync
    path('ecommerce/<uuid:platform_id>/sync/products/', views.sync_ecommerce_products, name='sync-ecommerce-products'),
    path('ecommerce/<uuid:platform_id>/sync/inventory/', views.sync_ecommerce_inventory, name='sync-ecommerce-inventory'),
    path('ecommerce/<uuid:platform_id>/sync/orders/', views.sync_ecommerce_orders, name='sync-ecommerce-orders'),
    path('ecommerce/<uuid:platform_id>/sync/status/', views.get_ecommerce_sync_status, name='get-ecommerce-sync-status'),
]