from django.contrib import admin
from django.contrib.auth.models import User
from .models import (
    # User Management
    UserProfile,
    Permission,
    PermissionGroup,
    
    # Core Models
    Category,
    Product,
    ProductVariant,
    Warehouse,
    Location,
    Bin,
    Inventory,
    Customer,
    
    # Sales & Orders
    Sale,
    SaleLine,
    Payment,
    
    # Transfers
    Transfer,
    TransferLine,
    
    # Returns & Exchanges
    Return,
    ReturnLine,
    
    # Promotions
    Promotion,
    Coupon,
    
    # Purchasing
    PurchaseOrder,
    PurchaseOrderLine,
    GoodsReceivedNote,
    GoodsReceivedNoteLine,
    
    # System
    BlacklistedToken,
    Webhook,
    WebhookLog,
    AuditLog,
    
    # Payment & Integration
    PaymentToken,
    PaymentGatewayConfig,
    EcommercePlatform,
    EcommerceSyncLog,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'store_credit', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'description']
    search_fields = ['name', 'codename']


@admin.register(PermissionGroup)
class PermissionGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    filter_horizontal = ['permissions']
    search_fields = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'sku', 'barcode']
    list_editable = ['price', 'is_active']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'sku', 'additional_price']
    search_fields = ['name', 'sku', 'product__name']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'warehouse_type', 'is_active', 'created_at']
    list_filter = ['warehouse_type', 'is_active']
    search_fields = ['name', 'location']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'warehouse', 'code', 'is_active']
    list_filter = ['warehouse', 'is_active']
    search_fields = ['name', 'code', 'warehouse__name']


@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'code', 'is_active']
    list_filter = ['location', 'is_active']
    search_fields = ['name', 'code', 'location__name']


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'qty_on_hand', 'qty_reserved', 'available_stock', 'last_updated']
    list_filter = ['warehouse', 'product__category']
    search_fields = ['product__name', 'warehouse__name', 'location__code']
    raw_id_fields = ['product', 'warehouse', 'location', 'bin']
    
    def available_stock(self, obj):
        return obj.available_stock()
    available_stock.short_description = 'Available Stock'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone', 'loyalty_points', 'store_credit', 'is_active']
    list_filter = ['is_active']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    list_editable = ['is_active']


# Inline for Sale Lines
class SaleLineInline(admin.TabularInline):
    model = SaleLine
    extra = 1
    raw_id_fields = ['product', 'variant']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'cashier', 'customer', 'warehouse', 'total_amount', 'payment_status', 'sale_date']
    list_filter = ['payment_status', 'sale_type', 'sale_date', 'warehouse']
    search_fields = ['receipt_number', 'cashier__username', 'customer__first_name', 'customer__last_name']
    inlines = [SaleLineInline]
    readonly_fields = ['sale_date', 'completed_at', 'original_total']
    raw_id_fields = ['cashier', 'customer', 'warehouse']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['sale', 'payment_method', 'amount', 'paid_at']
    list_filter = ['payment_method', 'paid_at']
    search_fields = ['sale__receipt_number', 'reference']
    raw_id_fields = ['sale']


# Inline for Transfer Lines
class TransferLineInline(admin.TabularInline):
    model = TransferLine
    extra = 1
    raw_id_fields = ['product', 'variant', 'from_inventory', 'to_inventory']


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ['transfer_number', 'from_warehouse', 'to_warehouse', 'status', 'requested_at', 'requested_by']
    list_filter = ['status', 'requested_at', 'from_warehouse', 'to_warehouse']
    search_fields = ['transfer_number', 'requested_by__username']
    inlines = [TransferLineInline]
    readonly_fields = ['requested_at', 'approved_at', 'received_at', 'completed_at']
    raw_id_fields = ['from_warehouse', 'to_warehouse', 'requested_by', 'approved_by']


# Inline for Return Lines
class ReturnLineInline(admin.TabularInline):
    model = ReturnLine
    extra = 1
    raw_id_fields = ['product', 'variant', 'original_line', 'exchange_product', 'exchange_variant']


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['return_number', 'original_sale', 'customer', 'return_type', 'status', 'total_amount', 'created_at']
    list_filter = ['return_type', 'status', 'created_at']
    search_fields = ['return_number', 'original_sale__receipt_number', 'customer__first_name', 'customer__last_name']
    inlines = [ReturnLineInline]
    readonly_fields = ['created_at', 'updated_at', 'processed_at', 'locked_at', 'original_total']
    raw_id_fields = ['original_sale', 'customer', 'processed_by']


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['name', 'promotion_type', 'discount_value', 'is_active', 'start_date', 'end_date']
    list_filter = ['promotion_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    filter_horizontal = ['products', 'categories', 'customer_groups', 'required_products', 'bonus_products']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'coupon_type', 'discount_value', 'is_valid', 'start_date', 'end_date']
    list_filter = ['coupon_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['code']
    raw_id_fields = ['promotion']


# Inline for Purchase Order Lines
class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1
    raw_id_fields = ['product', 'variant', 'destination_location', 'destination_bin']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'supplier', 'warehouse', 'status', 'total_amount', 'order_date', 'expected_delivery_date']
    list_filter = ['status', 'order_date', 'warehouse']
    search_fields = ['po_number', 'supplier__username']
    inlines = [PurchaseOrderLineInline]
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['supplier', 'warehouse', 'destination_location', 'destination_bin', 'approved_by']


# Inline for GRN Lines
class GoodsReceivedNoteLineInline(admin.TabularInline):
    model = GoodsReceivedNoteLine
    extra = 1
    raw_id_fields = ['purchase_order_line', 'destination_location', 'destination_bin']


@admin.register(GoodsReceivedNote)
class GoodsReceivedNoteAdmin(admin.ModelAdmin):
    list_display = ['grn_number', 'purchase_order', 'received_by', 'received_date', 'verified']
    list_filter = ['received_date', 'verified']
    search_fields = ['grn_number', 'purchase_order__po_number', 'received_by__username']
    inlines = [GoodsReceivedNoteLineInline]
    readonly_fields = ['created_at']
    raw_id_fields = ['purchase_order', 'received_by', 'verified_by']


@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(admin.ModelAdmin):
    list_display = ['jti', 'user', 'blacklisted_at', 'expires_at']
    list_filter = ['blacklisted_at', 'expires_at']
    search_fields = ['jti', 'user__username']
    readonly_fields = ['blacklisted_at']


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ['name', 'target_url', 'event_type', 'is_active', 'created_at']
    list_filter = ['event_type', 'is_active', 'created_at']
    search_fields = ['name', 'target_url']


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['webhook', 'timestamp', 'success', 'response_status']
    list_filter = ['success', 'timestamp', 'response_status']
    search_fields = ['webhook__name']
    readonly_fields = ['timestamp']
    raw_id_fields = ['webhook']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'object_type', 'object_id', 'timestamp']
    list_filter = ['action', 'object_type', 'timestamp']
    search_fields = ['user__username', 'object_repr']
    readonly_fields = ['timestamp']
    raw_id_fields = ['user']


@admin.register(PaymentToken)
class PaymentTokenAdmin(admin.ModelAdmin):
    list_display = ['customer', 'gateway', 'masked_card_number', 'is_default', 'is_active', 'created_at']
    list_filter = ['gateway', 'is_default', 'is_active', 'created_at']
    search_fields = ['customer__first_name', 'customer__last_name', 'token']
    raw_id_fields = ['customer']


@admin.register(PaymentGatewayConfig)
class PaymentGatewayConfigAdmin(admin.ModelAdmin):
    list_display = ['gateway', 'is_sandbox', 'is_active', 'created_at']
    list_filter = ['gateway', 'is_sandbox', 'is_active']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EcommercePlatform)
class EcommercePlatformAdmin(admin.ModelAdmin):
    list_display = ['name', 'platform', 'is_active', 'last_sync', 'created_at']
    list_filter = ['platform', 'is_active', 'sync_products', 'sync_inventory', 'sync_orders']
    search_fields = ['name', 'platform']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(EcommerceSyncLog)
class EcommerceSyncLogAdmin(admin.ModelAdmin):
    list_display = ['platform', 'sync_type', 'status', 'records_synced', 'started_at']
    list_filter = ['sync_type', 'status', 'started_at']
    search_fields = ['platform__name']
    readonly_fields = ['started_at', 'completed_at']
    raw_id_fields = ['platform']