from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('warehouse_manager', 'Warehouse Manager'),
        ('store_manager', 'Store Manager'),
        ('cashier', 'Cashier'),
        ('accountant', 'Accountant'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cashier')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    def clean(self):
        if self.role not in dict(self.ROLE_CHOICES):
            raise ValidationError(f"Invalid role: {self.role}")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when a new user is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
    else:
        # Create profile if it doesn't exist
        UserProfile.objects.get_or_create(user=instance)


# Rest of your models remain largely the same, just ensure they have proper validation
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def clean(self):
        if not self.name.strip():
            raise ValidationError("Category name cannot be empty.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, blank=True, unique=True, null=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def clean(self):
        if not self.name.strip():
            raise ValidationError("Product name cannot be empty.")
        if not self.sku.strip():
            raise ValidationError("SKU cannot be empty.")
        if self.price <= 0:
            raise ValidationError("Price must be greater than zero.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)



class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, blank=True, unique=True, null=True)
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['product', 'name']]

    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    def clean(self):
        if not self.name.strip():
            raise ValidationError("Variant name cannot be empty.")
        if not self.sku.strip():
            raise ValidationError("SKU cannot be empty.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def clean(self):
        if not self.name.strip():
            raise ValidationError("Warehouse name cannot be empty.")
        if not self.location.strip():
            raise ValidationError("Location cannot be empty.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    qty_on_hand = models.PositiveIntegerField(default=0)
    qty_reserved = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['product', 'variant', 'warehouse']]
        verbose_name_plural = "Inventories"

    def available_stock(self):
        return max(0, self.qty_on_hand - self.qty_reserved)
    
    def is_low_stock(self):
        return self.available_stock() <= self.min_stock_level
    
    def clean(self):
        if self.qty_reserved > self.qty_on_hand:
            raise ValidationError("Reserved quantity cannot exceed quantity on hand.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        variant_str = f" - {self.variant.name}" if self.variant else ""
        return f"{self.product.name}{variant_str} - {self.warehouse.name}: {self.qty_on_hand}"


class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    loyalty_points = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def clean(self):
        if not self.first_name.strip() or not self.last_name.strip():
            raise ValidationError("First name and last name are required.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Sale(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('partially_paid', 'Partially Paid'),
    ]
    
    SALE_TYPE_CHOICES = [
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('exchange', 'Exchange'),
    ]

    receipt_number = models.CharField(max_length=100, unique=True)
    cashier = models.ForeignKey(User, on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    sale_type = models.CharField(max_length=10, choices=SALE_TYPE_CHOICES, default='sale')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    sale_date = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Sale {self.receipt_number}"
    
    def amount_paid(self):
        return sum(payment.amount for payment in self.payments.all())
    
    def balance_due(self):
        return self.total_amount - self.amount_paid()
    
    def clean(self):
        if self.total_amount <= 0:
            raise ValidationError("Total amount must be greater than zero.")
        if self.tax_amount < 0:
            raise ValidationError("Tax amount cannot be negative.")
        if self.discount_amount < 0:
            raise ValidationError("Discount amount cannot be negative.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class SaleLine(models.Model):
    sale = models.ForeignKey(Sale, related_name='lines', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        variant_str = f" - {self.variant.name}" if self.variant else ""
        return f"{self.quantity}x {self.product.name}{variant_str}"
    
    def profit(self):
        if self.cost_price:
            return (self.unit_price - self.cost_price) * self.quantity
        return None
    
    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        if self.unit_price <= 0:
            raise ValidationError("Unit price must be greater than zero.")
        if self.total_price <= 0:
            raise ValidationError("Total price must be greater than zero.")
        if not (0 <= self.discount_percent <= 100):
            raise ValidationError("Discount percent must be between 0 and 100.")
    
    def save(self, *args, **kwargs):
        # Calculate total price if not set
        if not self.total_price:
            discount_factor = (100 - self.discount_percent) / 100
            self.total_price = self.quantity * self.unit_price * discount_factor
        
        # Set cost price if not set
        if not self.cost_price and self.product.cost_price:
            self.cost_price = self.product.cost_price
        
        self.clean()
        super().save(*args, **kwargs)


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'Mobile Payment'),
        ('voucher', 'Voucher'),
        ('credit', 'Credit'),
        ('mixed', 'Mixed'),
    ]

    sale = models.ForeignKey(Sale, related_name='payments', on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=200, blank=True)
    paid_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.payment_method} - {self.amount}"
    
    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Payment amount must be greater than zero.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Transfer(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('in_transit', 'In Transit'),
        ('received', 'Received'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    transfer_number = models.CharField(max_length=100, unique=True)
    from_warehouse = models.ForeignKey(Warehouse, related_name='transfers_from', on_delete=models.PROTECT)
    to_warehouse = models.ForeignKey(Warehouse, related_name='transfers_to', on_delete=models.PROTECT)
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT)
    approved_by = models.ForeignKey(User, related_name='approved_transfers', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Transfer {self.transfer_number}"
    
    def total_items(self):
        return sum(line.requested_qty for line in self.lines.all())
    
    def clean(self):
        if self.from_warehouse == self.to_warehouse:
            raise ValidationError("Source and destination warehouses cannot be the same.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class TransferLine(models.Model):
    transfer = models.ForeignKey(Transfer, related_name='lines', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    requested_qty = models.PositiveIntegerField()
    transferred_qty = models.PositiveIntegerField(default=0)
    received_qty = models.PositiveIntegerField(default=0)

    def __str__(self):
        variant_str = f" - {self.variant.name}" if self.variant else ""
        return f"{self.requested_qty}x {self.product.name}{variant_str}"
    
    def clean(self):
        if self.requested_qty <= 0:
            raise ValidationError("Requested quantity must be greater than zero.")
        if self.transferred_qty > self.requested_qty:
            raise ValidationError("Transferred quantity cannot exceed requested quantity.")
        if self.received_qty > self.transferred_qty:
            raise ValidationError("Received quantity cannot exceed transferred quantity.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Return(models.Model):
    RETURN_TYPE_CHOICES = [
        ('return', 'Return'),
        ('exchange', 'Exchange'),
        ('refund', 'Refund'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ]

    return_number = models.CharField(max_length=100, unique=True)
    original_sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name='returns')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    return_type = models.CharField(max_length=20, choices=RETURN_TYPE_CHOICES, default='return')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refunded_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='returns_processed')
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.return_type.title()} {self.return_number}"
    
    def clean(self):
        if self.total_amount < 0:
            raise ValidationError("Total amount cannot be negative.")
        if self.refund_amount < 0:
            raise ValidationError("Refund amount cannot be negative.")
        if self.refund_amount > self.total_amount:
            raise ValidationError("Refund amount cannot exceed total amount.")
    
    def save(self, *args, **kwargs):
        self.clean()
        if not self.return_number:
            import uuid
            self.return_number = f"RET-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class ReturnLine(models.Model):
    return_obj = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='lines')
    original_line = models.ForeignKey(SaleLine, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_returned = models.BooleanField(default=False)
    # For exchange: details of the new product
    exchange_product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True, related_name='exchanges_as_new')
    exchange_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True, related_name='exchanges_as_new')
    exchange_quantity = models.PositiveIntegerField(null=True, blank=True)
    exchange_unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        if self.unit_price <= 0:
            raise ValidationError("Unit price must be greater than zero.")
        if self.total_price <= 0:
            raise ValidationError("Total price must be greater than zero.")
    
    def save(self, *args, **kwargs):
        self.clean()
        if not self.total_price:
            self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Promotion(models.Model):
    PROMOTION_TYPE_CHOICES = [
        ('percentage', 'Percentage Discount'),
        ('fixed_amount', 'Fixed Amount Discount'),
        ('buy_x_get_y', 'Buy X Get Y'),
        ('bundle', 'Bundle Deal'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)  # For percentage or fixed amount
    # For buy_x_get_y
    buy_quantity = models.PositiveIntegerField(null=True, blank=True)
    get_quantity = models.PositiveIntegerField(null=True, blank=True)
    # For bundle deals
    required_products = models.ManyToManyField(Product, related_name='required_for_promotions', blank=True)
    bonus_products = models.ManyToManyField(Product, related_name='bonus_for_promotions', blank=True)
    
    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Customer groups (for tiered pricing)
    customer_groups = models.ManyToManyField('auth.Group', blank=True)
    
    # Category and product restrictions
    categories = models.ManyToManyField(Category, blank=True)
    products = models.ManyToManyField(Product, blank=True, related_name='promotions')
    
    # Minimum order value
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Usage limits
    max_usage_count = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return (self.is_active and 
                self.start_date <= now <= self.end_date and
                (self.max_usage_count is None or self.used_count < self.max_usage_count))
    
    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date.")
        if self.promotion_type in ['percentage', 'fixed_amount'] and self.discount_value <= 0:
            raise ValidationError("Discount value must be greater than zero.")
        if self.min_order_value < 0:
            raise ValidationError("Minimum order value cannot be negative.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Coupon(models.Model):
    CODE_TYPE_CHOICES = [
        ('percentage', 'Percentage Discount'),
        ('fixed_amount', 'Fixed Amount Discount'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, null=True, blank=True)
    coupon_type = models.CharField(max_length=20, choices=CODE_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Usage limits
    max_usage_count = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    
    # One-time use per customer
    is_limited_to_customer = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code
    
    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return (self.is_active and 
                self.start_date <= now <= self.end_date and
                (self.max_usage_count is None or self.used_count < self.max_usage_count))
    
    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date.")
        if self.discount_value <= 0:
            raise ValidationError("Discount value must be greater than zero.")
    
    def save(self, *args, **kwargs):
        self.clean()
        if not self.code:
            import uuid
            self.code = f"COUP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('ordered', 'Ordered'),
        ('in_transit', 'In Transit'),
        ('partially_received', 'Partially Received'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_orders')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Financials
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Dates
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)
    
    # Approval
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_purchase_orders')
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    shipping_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PO-{self.po_number}"
    
    def calculate_totals(self):
        """Calculate and update the totals for this purchase order"""
        subtotal = 0
        for line in self.lines.all():
            subtotal += line.total_price
        self.subtotal = subtotal
        self.total_amount = subtotal + self.tax_amount + self.shipping_cost
        self.save()
    
    def clean(self):
        if self.expected_delivery_date and self.order_date >= self.expected_delivery_date:
            raise ValidationError("Expected delivery date must be after order date.")
        if self.shipping_cost < 0 or self.tax_amount < 0:
            raise ValidationError("Shipping cost and tax amount cannot be negative.")
    
    def save(self, *args, **kwargs):
        self.clean()
        if not self.po_number:
            import uuid
            self.po_number = f"PO-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class PurchaseOrderLine(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    
    # Order quantities
    ordered_qty = models.PositiveIntegerField()
    received_qty = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Tracking quantities that have been processed to inventory
    processed_qty = models.PositiveIntegerField(default=0)  # Qty that has been added to inventory
    
    # Discount
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    def __str__(self):
        variant_str = f" - {self.variant.name}" if self.variant else ""
        return f"{self.ordered_qty}x {self.product.name}{variant_str}"
    
    @property
    def remaining_qty(self):
        """Quantity that still needs to be received"""
        return self.ordered_qty - self.received_qty
    
    @property
    def remaining_to_process(self):
        """Quantity that has been received but not yet processed to inventory"""
        return self.received_qty - self.processed_qty
    
    def clean(self):
        if self.ordered_qty <= 0:
            raise ValidationError("Ordered quantity must be greater than zero.")
        if self.unit_cost <= 0:
            raise ValidationError("Unit cost must be greater than zero.")
        if self.discount_percent < 0 or self.discount_percent > 100:
            raise ValidationError("Discount percent must be between 0 and 100.")
        if self.received_qty > self.ordered_qty:
            raise ValidationError("Received quantity cannot exceed ordered quantity.")
        if self.processed_qty > self.received_qty:
            raise ValidationError("Processed quantity cannot exceed received quantity.")
    
    def save(self, *args, **kwargs):
        # Calculate total price if not set
        if not self.total_price:
            discount_factor = (100 - self.discount_percent) / 100
            self.total_price = self.ordered_qty * self.unit_cost * discount_factor
        
        self.clean()
        super().save(*args, **kwargs)


class GoodsReceivedNote(models.Model):
    """Record for when goods are received from suppliers"""
    grn_number = models.CharField(max_length=100, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='grns')
    received_by = models.ForeignKey(User, on_delete=models.PROTECT)
    received_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    # Verification
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_grns')
    verified_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"GRN-{self.grn_number}"
    
    def save(self, *args, **kwargs):
        if not self.grn_number:
            import uuid
            self.grn_number = f"GRN-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class GoodsReceivedNoteLine(models.Model):
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, related_name='lines')
    purchase_order_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.CASCADE)
    received_qty = models.PositiveIntegerField()
    condition = models.CharField(max_length=50, default='Good')  # Good, Damaged, Missing, etc.
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.received_qty}x {self.purchase_order_line.product.name} (GRN: {self.grn.grn_number})"
    
    def clean(self):
        if self.received_qty <= 0:
            raise ValidationError("Received quantity must be greater than zero.")
        if self.received_qty > self.purchase_order_line.remaining_qty:
            raise ValidationError("Received quantity cannot exceed remaining quantity in purchase order.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        # Update the purchase order line with received quantity
        self.purchase_order_line.received_qty += self.received_qty
        self.purchase_order_line.save()
        
        # Update purchase order status based on received quantities
        po = self.purchase_order_line.purchase_order
        total_ordered = sum(line.ordered_qty for line in po.lines.all())
        total_received = sum(line.received_qty for line in po.lines.all())
        
        if total_received == 0:
            po.status = 'ordered'
        elif total_received < total_ordered:
            po.status = 'partially_received'
        else:
            po.status = 'received'
        
        po.save()


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'View'),
        ('export', 'Export'),
        ('print', 'Print'),
        ('return', 'Return'),
        ('exchange', 'Exchange'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=255, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action} - {self.object_type} ({self.object_id})"
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['object_type', 'object_id']),
        ]