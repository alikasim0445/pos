from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
from django.conf import settings


class Permission(models.Model):
    """
    Represents a specific permission that can be assigned to roles or permission groups
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    codename = models.CharField(max_length=100, unique=True)  # e.g., 'add_sale', 'view_inventory'
    
    def __str__(self):
        return f"{self.name} ({self.codename})"


class PermissionGroup(models.Model):
    """
    A group of permissions that can be assigned to roles
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    
    def __str__(self):
        return self.name


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
    permission_groups = models.ManyToManyField(PermissionGroup, blank=True, help_text="Additional permission groups assigned to this user")
    
    # MFA fields
    is_mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True, null=True)
    backup_codes = models.TextField(blank=True, null=True, help_text="JSON string of backup codes")
    
    # Store credit
    store_credit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
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
    
    def get_all_permissions(self):
        """
        Get all permissions for this user based on their role and assigned permission groups
        """
        permissions = set()
        
        # Add permissions based on role
        role_permissions = self.get_role_based_permissions()
        permissions.update(role_permissions)
        
        # Add permissions from assigned groups
        for group in self.permission_groups.all():
            for permission in group.permissions.all():
                permissions.add(permission.codename)
        
        return permissions
    
    def get_role_based_permissions(self):
        """
        Return permissions based on the user's role
        """
        role_permissions = {
            'super_admin': [
                'add_user', 'change_user', 'delete_user', 'view_user',
                'add_sale', 'change_sale', 'delete_sale', 'view_sale',
                'add_product', 'change_product', 'delete_product', 'view_product',
                'add_category', 'change_category', 'delete_category', 'view_category',
                'add_warehouse', 'change_warehouse', 'delete_warehouse', 'view_warehouse',
                'add_inventory', 'change_inventory', 'delete_inventory', 'view_inventory',
                'add_customer', 'change_customer', 'delete_customer', 'view_customer',
                'add_payment', 'change_payment', 'delete_payment', 'view_payment',
                'add_transfer', 'change_transfer', 'delete_transfer', 'view_transfer',
                'add_return', 'change_return', 'delete_return', 'view_return',
                'add_promotion', 'change_promotion', 'delete_promotion', 'view_promotion',
                'add_coupon', 'change_coupon', 'delete_coupon', 'view_coupon',
                'add_purchaseorder', 'change_purchaseorder', 'delete_purchaseorder', 'view_purchaseorder',
                'add_grn', 'change_grn', 'delete_grn', 'view_grn',
                'view_sales_report', 'view_inventory_report', 'view_profitability_report', 'view_transfer_report',
                'assign_roles', 'manage_permissions', 'view_user_activity', 'export_data',
                'reset_passwords', 'activate_deactivate_users'
            ],
            'admin': [
                'add_user', 'change_user', 'view_user',
                'add_sale', 'change_sale', 'view_sale',
                'add_product', 'change_product', 'view_product',
                'add_category', 'change_category', 'view_category',
                'add_warehouse', 'change_warehouse', 'view_warehouse',
                'add_inventory', 'change_inventory', 'view_inventory',
                'add_customer', 'change_customer', 'view_customer',
                'add_payment', 'change_payment', 'view_payment',
                'add_transfer', 'change_transfer', 'view_transfer',
                'add_return', 'change_return', 'view_return',
                'add_promotion', 'change_promotion', 'view_promotion',
                'add_coupon', 'change_coupon', 'view_coupon',
                'add_purchaseorder', 'change_purchaseorder', 'view_purchaseorder',
                'add_grn', 'change_grn', 'view_grn',
                'view_sales_report', 'view_inventory_report', 'view_profitability_report', 'view_transfer_report',
                'view_user_activity', 'export_data'
            ],
            'store_manager': [
                'add_sale', 'view_sale',
                'add_product', 'view_product',
                'add_category', 'view_category',
                'add_warehouse', 'view_warehouse',
                'add_inventory', 'change_inventory', 'view_inventory',
                'add_customer', 'change_customer', 'view_customer',
                'add_payment', 'change_payment', 'view_payment',
                'add_transfer', 'change_transfer', 'view_transfer',
                'add_return', 'change_return', 'view_return',
                'view_sales_report', 'view_inventory_report', 'view_store_reports',
                'approve_transfers', 'export_data'
            ],
            'warehouse_manager': [
                'view_inventory', 'change_inventory',
                'add_transfer', 'view_transfer',
                'view_warehouse_reports', 'export_data'
            ],
            'cashier': [
                'add_sale', 'view_sale',
                'add_payment', 'view_payment',
                'view_product', 'view_inventory'
            ],
            'accountant': [
                'view_sales', 'view_inventory', 'view_financial_reports',
                'view_profitability', 'export_data', 'view_payment_reports', 'view_expense_reports',
                'view_sales_report', 'view_inventory_report', 'view_profitability_report'
            ]
        }
        
        return role_permissions.get(self.role, [])
    
    def has_permission(self, permission_codename):
        """
        Check if the user has a specific permission
        Super admins and users with is_superuser flag have all permissions
        """
        # Super admins and Django superusers have all permissions
        if self.role == 'super_admin' or (hasattr(self.user, 'is_superuser') and self.user.is_superuser):
            return True
            
        return permission_codename in self.get_all_permissions()


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
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Default retail price
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Wholesale price
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_wholesale_qty = models.PositiveIntegerField(default=1, help_text="Minimum quantity for wholesale pricing")
    effective_date = models.DateTimeField(default=timezone.now, help_text="Date when current prices became effective", blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)  # Product image
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags for the product")  # Product tags
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
    WAREHOUSE_TYPE_CHOICES = [
        ('warehouse', 'Warehouse'),
        ('store', 'Store Location'),
        ('distribution_center', 'Distribution Center'),
        ('depot', 'Depot'),
    ]
    
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, help_text="Address or general location of the warehouse/store")
    warehouse_type = models.CharField(max_length=20, choices=WAREHOUSE_TYPE_CHOICES, default='warehouse')
    contact_person = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    capacity = models.PositiveIntegerField(default=0, help_text="Maximum capacity in units or volume")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Geographic coordinates (optional)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.name
    
    def clean(self):
        if not self.name.strip():
            raise ValidationError("Warehouse name cannot be empty.")
        if not self.location.strip():
            raise ValidationError("Location cannot be empty.")
        # Check if a warehouse with the same name and location already exists (only for new objects)
        if not self.pk:  # Only check for new objects
            existing = Warehouse.objects.filter(name=self.name, location=self.location).first()
            if existing:
                raise ValidationError(f"Warehouse with name '{self.name}' and location '{self.location}' already exists.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def can_delete(self):
        """
        Check if this warehouse can be deleted based on existing dependencies.
        """
        from django.db.models import Q
        from .models import Inventory, Transfer, Sale
        
        # Check if there are any inventory items in this warehouse
        if Inventory.objects.filter(warehouse=self).exists():
            return False, "Cannot delete warehouse with existing inventory items"
        
        # Check if there are any transfers from or to this warehouse
        if Transfer.objects.filter(Q(from_warehouse=self) | Q(to_warehouse=self)).exists():
            return False, "Cannot delete warehouse with existing transfers"
        
        # Check if there are any sales associated with this warehouse
        if Sale.objects.filter(warehouse=self).exists():
            return False, "Cannot delete warehouse with existing sales"
        
        return True, "Can delete warehouse"
        
    def delete_with_dependencies(self, force=False):
        """
        Delete warehouse with its dependencies if force=True, otherwise check if safe to delete
        """
        if not force:
            can_delete, message = self.can_delete()
            if not can_delete:
                raise ValidationError(message)
        
        # If force=True, we delete dependencies first, then the warehouse
        if force:
            from .models import Inventory, Transfer, Sale, Location, Bin
            
            # Delete related inventory items
            Inventory.objects.filter(warehouse=self).delete()
            
            # Delete related transfers
            Transfer.objects.filter(Q(from_warehouse=self) | Q(to_warehouse=self)).delete()
            
            # Delete related sales
            Sale.objects.filter(warehouse=self).delete()
            
            # Delete related locations and bins
            Bin.objects.filter(location__warehouse=self).delete()
            Location.objects.filter(warehouse=self).delete()
        
        # Delete the warehouse itself
        super().delete()


class Location(models.Model):
    """
    Represents a specific location within a warehouse or store (e.g., aisle, section, room).
    This allows for hierarchical organization within a warehouse.
    """
    name = models.CharField(max_length=255, help_text="Name of the location (e.g., Aisle A, Section 1, Back Room)")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='locations')
    code = models.CharField(max_length=50, help_text="Unique code for the location within the warehouse (e.g., A-01, SEC-001)")
    description = models.TextField(blank=True, help_text="Detailed description of the location")
    parent_location = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                      related_name='sub_locations', 
                                      help_text="Parent location if this is a sub-location")
    capacity = models.PositiveIntegerField(default=0, help_text="Maximum capacity for this location")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['warehouse', 'code']]
        verbose_name_plural = "Locations"
        ordering = ['warehouse', 'code']

    def __str__(self):
        return f"{self.warehouse.name} - {self.name} ({self.code})"

    def clean(self):
        if not self.name.strip():
            raise ValidationError("Location name cannot be empty.")
        if not self.code.strip():
            raise ValidationError("Location code cannot be empty.")
        # Prevent circular parent references
        if self.parent_location:
            current = self.parent_location
            while current:
                if current == self:
                    raise ValidationError("Cannot set parent location that creates a circular reference.")
                current = current.parent_location

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_inventory(self):
        """
        Get all inventory items in this location
        """
        return Inventory.objects.filter(location=self).select_related(
            'product', 'warehouse', 'bin'
        )


class Bin(models.Model):
    """
    Represents a specific bin or shelf within a location.
    This is the most granular level for inventory tracking.
    """
    name = models.CharField(max_length=255, help_text="Name of the bin (e.g., Shelf 1, Bin A-01)")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='bins')
    code = models.CharField(max_length=50, help_text="Unique code for the bin within the location (e.g., B-01-01)")
    description = models.TextField(blank=True, help_text="Detailed description of the bin")
    capacity = models.PositiveIntegerField(default=0, help_text="Maximum capacity for this bin")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['location', 'code']]
        verbose_name_plural = "Bins"
        ordering = ['location', 'code']

    def __str__(self):
        return f"{self.location.warehouse.name} - {self.location.code} - {self.name}"

    def clean(self):
        if not self.name.strip():
            raise ValidationError("Bin name cannot be empty.")
        if not self.code.strip():
            raise ValidationError("Bin code cannot be empty.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_inventory(self):
        """
        Get all inventory items in this bin
        """
        return Inventory.objects.filter(bin=self).select_related(
            'product', 'warehouse', 'location'
        )


class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, help_text="Warehouse/Store where this inventory is located")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='inventory_items',
                                help_text="Specific location within the warehouse (optional, for advanced tracking)")
    bin = models.ForeignKey(Bin, on_delete=models.SET_NULL, null=True, blank=True, 
                           related_name='inventory_items',
                           help_text="Specific bin/shelf within the location (optional, for advanced tracking)")
    bin_location = models.CharField(max_length=50, blank=True, help_text="Legacy bin location field (deprecated in favor of Bin model)")
    qty_on_hand = models.PositiveIntegerField(default=0)
    qty_reserved = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['product', 'variant', 'warehouse', 'location', 'bin']]  # More granular tracking
        verbose_name_plural = "Inventories"

    def available_stock(self):
        return max(0, self.qty_on_hand - self.qty_reserved)
    
    def is_low_stock(self):
        return self.available_stock() <= self.min_stock_level
    
    def clean(self):
        if self.qty_reserved > self.qty_on_hand:
            raise ValidationError("Reserved quantity cannot exceed quantity on hand.")
        # Validate location/warehouse consistency
        if self.location and self.location.warehouse != self.warehouse:
            raise ValidationError("Selected location must belong to the selected warehouse.")
        # Validate bin/location consistency
        if self.bin and self.bin.location != self.location:
            raise ValidationError("Selected bin must belong to the selected location.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        variant_str = f" - {self.variant.name}" if self.variant else ""
        location_str = f" - {self.location.code}" if self.location else ""
        bin_str = f" - {self.bin.code}" if self.bin else ""
        return f"{self.product.name}{variant_str} - {self.warehouse.name}{location_str}{bin_str}: {self.qty_on_hand}"

    @classmethod
    def get_inventory_by_location(cls, warehouse=None, location=None, product=None):
        """
        Helper method to get inventory items filtered by location and/or product
        """
        queryset = cls.objects.select_related('product', 'warehouse', 'location', 'bin')
        
        if warehouse:
            queryset = queryset.filter(warehouse=warehouse)
        if location:
            queryset = queryset.filter(location=location)
        if product:
            queryset = queryset.filter(product=product)
            
        return queryset


class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Additional notes about the customer")
    loyalty_points = models.IntegerField(default=0)
    store_credit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
    
    def earn_loyalty_points(self, points):
        """
        Add loyalty points to the customer's account
        """
        if points > 0:
            self.loyalty_points += points
            self.save()
            return self.loyalty_points
        else:
            raise ValidationError("Points to earn must be greater than zero.")
    
    def redeem_loyalty_points(self, points):
        """
        Redeem loyalty points from the customer's account
        """
        if points > 0:
            if points <= self.loyalty_points:
                self.loyalty_points -= points
                self.save()
                return self.loyalty_points
            else:
                raise ValidationError(f"Insufficient loyalty points. Customer has {self.loyalty_points} points, but tried to redeem {points} points.")
        else:
            raise ValidationError("Points to redeem must be greater than zero.")
    
    def calculate_loyalty_points_from_purchase(self, purchase_amount):
        """
        Calculate loyalty points earned from a purchase (1 point per $1 spent)
        """
        return int(purchase_amount)  # 1 point per dollar spent


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
    
    # Fields to ensure immutability after completion
    is_locked = models.BooleanField(default=False, help_text="Indicates if the sale record is locked and immutable after completion")
    locked_at = models.DateTimeField(null=True, blank=True, help_text="When the record was locked for immutability")
    original_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Original total amount before any changes (for audit purposes)")

    def __str__(self):
        return f"Sale {self.receipt_number}"
    
    def amount_paid(self):
        return sum(payment.amount for payment in self.payments.all())
    
    def balance_due(self):
        return self.total_amount - self.amount_paid()
    
    def update_payment_status(self):
        """
        Update the payment status based on the amount paid vs total amount
        """
        amount_paid = self.amount_paid()
        
        if amount_paid <= 0:
            # No payment made yet
            self.payment_status = 'pending'
        elif amount_paid >= self.total_amount:
            # Full payment received
            self.payment_status = 'completed'
        elif 0 < amount_paid < self.total_amount:
            # Partial payment
            self.payment_status = 'partially_paid'
        else:
            # Overpaid scenario (shouldn't happen with proper validation)
            self.payment_status = 'completed'
        
        # Lock the sale record if it's a terminal status to ensure immutability
        if self.payment_status in ['completed', 'cancelled', 'refunded'] and not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
            # Store the original total to ensure audit trail
            if not self.original_total:
                self.original_total = self.total_amount
        
        self.save()
    
    def process_payments(self, payment_data_list):
        """
        Process multiple payments for this sale
        
        Args:
            payment_data_list: List of payment dictionaries with 'method', 'amount', and optional 'reference'
        """
        from django.db import transaction
        
        with transaction.atomic():
            # Calculate the total amount to be paid
            total_payment_amount = sum(p['amount'] for p in payment_data_list)
            
            # Validate that total payment doesn't exceed the sale total
            if total_payment_amount > self.total_amount:
                raise ValidationError(
                    f"Total payment amount (${total_payment_amount}) exceeds sale total (${self.total_amount})"
                )
            
            # Create payment records
            for payment_data in payment_data_list:
                Payment.objects.create(
                    sale=self,
                    payment_method=payment_data['method'],
                    amount=payment_data['amount'],
                    reference=payment_data.get('reference', ''),
                    # Note: paid_at will default to current time
                )
            
            # Update payment status
            self.update_payment_status()
    
    def clean(self):
        if self.total_amount <= 0:
            raise ValidationError("Total amount must be greater than zero.")
        if self.tax_amount < 0:
            raise ValidationError("Tax amount cannot be negative.")
        if self.discount_amount < 0:
            raise ValidationError("Discount amount cannot be negative.")
        
        # Prevent changes to locked sales
        if self.pk and self.is_locked:
            original_instance = Sale.objects.get(pk=self.pk)
            # Only allow changes to payment_status for completed sales
            if (self.total_amount != original_instance.total_amount or
                self.tax_amount != original_instance.tax_amount or
                self.discount_amount != original_instance.discount_amount or
                self.sale_type != original_instance.sale_type or
                self.warehouse != original_instance.warehouse or
                self.customer_id != original_instance.customer_id):
                
                # Create audit log for attempted unauthorized change
                from .signals import get_current_user
                current_user = get_current_user()
                
                AuditLog.objects.create(
                    user=current_user,
                    action='attempted_modification',
                    object_type='sale',
                    object_id=self.pk,
                    object_repr=f'Sale {self.receipt_number} (locked)',
                    old_values={
                        'total_amount': float(original_instance.total_amount),
                        'tax_amount': float(original_instance.tax_amount),
                        'discount_amount': float(original_instance.discount_amount),
                    },
                    new_values={
                        'total_amount': float(self.total_amount),
                        'tax_amount': float(self.tax_amount),
                        'discount_amount': float(self.discount_amount),
                    },
                    timestamp=timezone.now(),
                    notes='Attempted modification of locked sale record'
                )
                
                raise ValidationError("Cannot modify a locked sale record after completion.")
    
    def save(self, *args, **kwargs):
        # Store the old status to detect status changes
        old_status = None
        if self.pk:  # If this is an existing object
            old_sale = Sale.objects.get(pk=self.pk)
            old_status = old_sale.payment_status
        
        is_new = self.pk is None
        will_reserve_stock = getattr(settings, 'AUTO_RESERVE_SALE_STOCK', True)
        
        # Set original total for new sales
        if is_new and not self.original_total:
            self.original_total = self.total_amount
        
        self.clean()
        super().save(*args, **kwargs)
        
        # Automatically reserve stock for new pending sales if configured to do so
        if is_new and self.payment_status == 'pending' and will_reserve_stock:
            self.reserve_stock_for_sale()
        
        # Handle stock reservation based on payment status changes
        if old_status and old_status != self.payment_status:
            # If status changed to cancelled from pending, release reserved stock
            if old_status == 'pending' and self.payment_status == 'cancelled':
                self.release_reserved_stock()
            # If status changed to completed from pending, finalize the sale
            elif old_status == 'pending' and self.payment_status == 'completed':
                self.finalize_sale()
    
    def reserve_stock_for_sale(self):
        """
        Reserve stock for all items in the sale
        """
        from django.db import transaction
        with transaction.atomic():
            for line in self.lines.all():
                # Find the inventory record for this product at the sale warehouse
                inventory = Inventory.objects.filter(
                    product=line.product,
                    variant=line.variant,
                    warehouse=self.warehouse
                ).first()
                
                if inventory:
                    # Check if sufficient stock is available
                    available_stock = inventory.qty_on_hand - inventory.qty_reserved
                    if available_stock >= line.quantity:
                        # Reserve the stock by updating the reserved quantity
                        inventory.qty_reserved += line.quantity
                        inventory.save()
                    else:
                        raise ValidationError(
                            f"Insufficient stock for product {line.product.name}. "
                            f"Available: {available_stock}, Requested: {line.quantity}"
                        )
                else:
                    # Create an inventory record if it doesn't exist, with 0 on hand but reserve the quantity
                    # This is unusual but could happen if inventory tracking is not properly set up
                    inventory = Inventory.objects.create(
                        product=line.product,
                        variant=line.variant,
                        warehouse=self.warehouse,
                        qty_on_hand=0,
                        qty_reserved=line.quantity,
                        min_stock_level=0
                    )
    
    def release_reserved_stock(self):
        """
        Release previously reserved stock for this sale
        """
        from django.db import transaction
        with transaction.atomic():
            for line in self.lines.all():
                # Find and update the inventory record
                inventory = Inventory.objects.filter(
                    product=line.product,
                    variant=line.variant,
                    warehouse=self.warehouse
                ).first()
                
                if inventory:
                    # Release the reserved stock
                    inventory.qty_reserved = max(0, inventory.qty_reserved - line.quantity)
                    inventory.save()
    
    def finalize_sale(self):
        """
        Finalize the sale by reducing inventory quantities
        """
        from django.db import transaction
        with transaction.atomic():
            for line in self.lines.all():
                # Find and update the inventory record
                inventory = Inventory.objects.filter(
                    product=line.product,
                    variant=line.variant,
                    warehouse=self.warehouse
                ).first()
                
                if inventory:
                    # Reduce both on-hand and reserved quantities
                    inventory.qty_on_hand = max(0, inventory.qty_on_hand - line.quantity)
                    inventory.qty_reserved = max(0, inventory.qty_reserved - line.quantity)
                    inventory.save()
    
    @classmethod
    def select_fulfillment_warehouse(cls, product, quantity, customer_location=None, preferred_warehouses=None):
        """
        Select the best warehouse for fulfilling an order based on availability and other factors
        Supports round-robin or priority-based selection
        """
        # Get all warehouses that have the product in stock
        available_inventories = Inventory.objects.filter(
            product=product,
            qty_on_hand__gte=quantity
        ).select_related('warehouse')
        
        if preferred_warehouses:
            # Filter by preferred warehouses if specified
            available_inventories = available_inventories.filter(
                warehouse__in=preferred_warehouses
            )
        
        if customer_location:
            # If customer location is provided, prioritize warehouses based on proximity
            # For now, we'll sort by some criteria - in a real system, you might calculate distance
            available_inventories = available_inventories.order_by('warehouse__id')  # Basic priority
        else:
            # Default: Sort by warehouse ID to create a round-robin effect
            available_inventories = available_inventories.order_by('warehouse__id')
        
        # Get the first available warehouse (this implements basic round-robin)
        for inventory in available_inventories:
            # Check if there's sufficient available stock (not reserved)
            available_stock = inventory.qty_on_hand - inventory.qty_reserved
            if available_stock >= quantity:
                return inventory.warehouse
        
        # If no warehouse has sufficient stock, return None
        return None
    
    @classmethod
    def create_with_reservation(cls, receipt_number, cashier, warehouse, total_amount, 
                               tax_amount=0, discount_amount=0, customer=None, 
                               sale_type='sale', notes='', lines_data=None):
        """
        Create a sale with automatic stock reservation
        """
        from django.db import transaction
        
        if lines_data is None:
            lines_data = []
        
        with transaction.atomic():
            # Create the sale with pending status
            sale = cls.objects.create(
                receipt_number=receipt_number,
                cashier=cashier,
                customer=customer,
                warehouse=warehouse,
                sale_type=sale_type,
                total_amount=total_amount,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                payment_status='pending',  # Start with pending
                notes=notes
            )
            
            # Create the sale lines
            for line_data in lines_data:
                SaleLine.objects.create(
                    sale=sale,
                    product=line_data['product'],
                    variant=line_data.get('variant'),
                    quantity=line_data['quantity'],
                    unit_price=line_data['unit_price'],
                    total_price=line_data.get('total_price'),
                    discount_percent=line_data.get('discount_percent', 0),
                    cost_price=line_data.get('cost_price')
                )
            
            # Reserve stock for the sale (this will be done automatically by the save method,
            # but we call it explicitly to ensure it happens)
            sale.reserve_stock_for_sale()
            
            return sale
    
    @classmethod
    def create_online_order(cls, receipt_number, customer, total_amount,
                           tax_amount=0, discount_amount=0, 
                           sale_type='sale', notes='', lines_data=None,
                           customer_location=None, preferred_warehouses=None):
        """
        Create an online order with warehouse selection based on availability
        Implements round-robin or priority-based warehouse fulfillment
        """
        from django.db import transaction
        import uuid
        
        if lines_data is None:
            lines_data = []
        
        with transaction.atomic():
            # Select warehouse for fulfillment based on availability and other factors
            selected_warehouse = None
            all_available = True
            
            for line_data in lines_data:
                product = line_data['product']
                quantity = line_data['quantity']
                
                # Find the best warehouse for this product
                product_warehouse = cls.select_fulfillment_warehouse(
                    product, quantity, customer_location, preferred_warehouses
                )
                
                if not product_warehouse:
                    raise ValidationError(f"Insufficient stock available for product {product.name}")
                
                # For mixed fulfillment orders, we might want to handle each item separately
                # For now, let's use the first item's warehouse as the main warehouse
                if selected_warehouse is None:
                    selected_warehouse = product_warehouse
                elif selected_warehouse != product_warehouse:
                    # If different items need to come from different warehouses,
                    # we might want to create separate orders or handle this differently
                    # For now, let's use round-robin and pick the first available warehouse
                    pass
            
            # If all items can be fulfilled from the same warehouse or we just need any warehouse
            if not selected_warehouse and lines_data:
                # If we couldn't determine a warehouse, just use the first product's available warehouse
                first_line = lines_data[0]
                selected_warehouse = cls.select_fulfillment_warehouse(
                    first_line['product'], first_line['quantity'], customer_location, preferred_warehouses
                )
                
                if not selected_warehouse:
                    raise ValidationError(f"No warehouse available for the requested products")
            
            # Create the online order sale
            sale = cls.objects.create(
                receipt_number=receipt_number,
                cashier=customer.user if hasattr(customer, 'user') else None,  # Use customer user if available
                customer=customer,
                warehouse=selected_warehouse,
                sale_type=sale_type,
                total_amount=total_amount,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                payment_status='pending',
                notes=notes
            )
            
            # Create the sale lines
            for line_data in lines_data:
                SaleLine.objects.create(
                    sale=sale,
                    product=line_data['product'],
                    variant=line_data.get('variant'),
                    quantity=line_data['quantity'],
                    unit_price=line_data['unit_price'],
                    total_price=line_data.get('total_price'),
                    discount_percent=line_data.get('discount_percent', 0),
                    cost_price=line_data.get('cost_price')
                )
            
            # Reserve stock for the sale
            sale.reserve_stock_for_sale()
            
            return sale


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
    from_location = models.ForeignKey(Location, related_name='transfers_from', on_delete=models.SET_NULL, null=True, blank=True,
                                    help_text="Source location within the warehouse (optional)")
    from_bin = models.ForeignKey(Bin, related_name='transfers_from', on_delete=models.SET_NULL, null=True, blank=True,
                                help_text="Source bin within the location (optional)")
    to_warehouse = models.ForeignKey(Warehouse, related_name='transfers_to', on_delete=models.PROTECT)
    to_location = models.ForeignKey(Location, related_name='transfers_to', on_delete=models.SET_NULL, null=True, blank=True,
                                  help_text="Destination location within the warehouse (optional)")
    to_bin = models.ForeignKey(Bin, related_name='transfers_to', on_delete=models.SET_NULL, null=True, blank=True,
                              help_text="Destination bin within the location (optional)")
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
            if self.from_location == self.to_location:
                if self.from_bin == self.to_bin:
                    raise ValidationError("Source and destination cannot be the same.")
        
        # Validate location/warehouse consistency
        if self.from_location and self.from_location.warehouse != self.from_warehouse:
            raise ValidationError("From location must belong to the from warehouse.")
        if self.to_location and self.to_location.warehouse != self.to_warehouse:
            raise ValidationError("To location must belong to the to warehouse.")
        # Validate bin/location consistency
        if self.from_bin and self.from_bin.location != self.from_location:
            raise ValidationError("From bin must belong to the from location.")
        if self.to_bin and self.to_bin.location != self.to_location:
            raise ValidationError("To bin must belong to the to location.")
    
    def save(self, *args, **kwargs):
        # Store the old status to detect status changes
        old_status = None
        if self.pk:  # If this is an existing object
            old_transfer = Transfer.objects.get(pk=self.pk)
            old_status = old_transfer.status
        
        is_new = self.pk is None
        will_reserve_stock = getattr(settings, 'AUTO_RESERVE_TRANSFER_STOCK', True)
        
        self.clean()
        super().save(*args, **kwargs)
        
        # Reserve stock automatically if configured to do so and this is a new transfer
        if is_new and self.status == 'requested' and will_reserve_stock:
            self.reserve_stock_for_transfer()
        # If status changed from 'requested' or 'approved' to 'cancelled', release stock
        elif (old_status in ['requested', 'approved'] and 
              self.status == 'cancelled'):
            self.release_reserved_stock()
        # If status changed to 'received', process the transfer
        elif (old_status in ['approved', 'in_transit'] and 
              self.status == 'received'):
            self.receive_transfer()
    
    def reserve_stock_for_transfer(self):
        """
        Reserve stock for all items in the transfer from the source inventory
        """
        for line in self.lines.all():
            # Find the source inventory record
            inventory = Inventory.objects.filter(
                product=line.product,
                variant=line.variant,
                warehouse=self.from_warehouse,
                location=self.from_location,
                bin=self.from_bin
            ).first()
            
            if inventory:
                # Check if sufficient stock is available
                available_stock = inventory.qty_on_hand - inventory.qty_reserved
                if available_stock >= line.requested_qty:
                    # Reserve the stock by updating the reserved quantity
                    inventory.qty_reserved += line.requested_qty
                    inventory.save()
                else:
                    raise ValidationError(
                        f"Insufficient stock for product {line.product.name}. "
                        f"Available: {available_stock}, Requested: {line.requested_qty}"
                    )
    
    def release_reserved_stock(self):
        """
        Release previously reserved stock for this transfer
        """
        for line in self.lines.all():
            # Find the source inventory record
            inventory = Inventory.objects.filter(
                product=line.product,
                variant=line.variant,
                warehouse=self.from_warehouse,
                location=self.from_location,
                bin=self.from_bin
            ).first()
            
            if inventory:
                # Release the reserved stock
                inventory.qty_reserved = max(0, inventory.qty_reserved - line.requested_qty)
                inventory.save()
    
    def receive_transfer(self):
        """
        Process the transfer receipt, moving inventory from source to destination
        """
        from django.db import transaction
        with transaction.atomic():
            for line in self.lines.all():
                # Find and update source inventory
                source_inventory = Inventory.objects.filter(
                    product=line.product,
                    variant=line.variant,
                    warehouse=self.from_warehouse,
                    location=self.from_location,
                    bin=self.from_bin
                ).first()
                
                if source_inventory:
                    # Reduce on-hand and reserved quantities in source
                    source_inventory.qty_on_hand = max(0, source_inventory.qty_on_hand - line.requested_qty)
                    source_inventory.qty_reserved = max(0, source_inventory.qty_reserved - line.requested_qty)
                    source_inventory.save()
                
                # Find or create destination inventory
                dest_inventory, created = Inventory.objects.get_or_create(
                    product=line.product,
                    variant=line.variant,
                    warehouse=self.to_warehouse,
                    location=self.to_location,
                    bin=self.to_bin,
                    defaults={
                        'qty_on_hand': 0,
                        'qty_reserved': 0,
                        'min_stock_level': 0
                    }
                )
                
                # Increase on-hand quantity at destination
                dest_inventory.qty_on_hand += line.requested_qty
                dest_inventory.save()
                
                # Update the transfer line to mark as received
                line.transferred_qty = line.requested_qty
                line.received_qty = line.requested_qty
                line.save()
    
    def cancel_transfer(self):
        """
        Cancel the transfer and release any reserved stock
        """
        if self.status in ['draft', 'requested']:
            self.release_reserved_stock()
            self.status = 'cancelled'
            self.save()
        elif self.status == 'approved':
            # If approved but not yet in transit, just cancel and release stock
            self.release_reserved_stock()
            self.status = 'cancelled'
            self.save()
        else:
            raise ValidationError(
                f"Cannot cancel transfer with status: {self.status}. "
                f"Transfer has already been processed."
            )


class TransferLine(models.Model):
    transfer = models.ForeignKey(Transfer, related_name='lines', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    requested_qty = models.PositiveIntegerField()
    transferred_qty = models.PositiveIntegerField(default=0)
    received_qty = models.PositiveIntegerField(default=0)
    from_inventory = models.ForeignKey(Inventory, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='transfer_out_lines',
                                     help_text="Specific inventory item to transfer from (optional)")
    to_inventory = models.ForeignKey(Inventory, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='transfer_in_lines',
                                    help_text="Specific inventory item to transfer to (optional)")

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
        # Validate inventory/transfer consistency
        if self.from_inventory and self.from_inventory.warehouse != self.transfer.from_warehouse:
            raise ValidationError("From inventory warehouse must match transfer's from warehouse.")
        if self.to_inventory and self.to_inventory.warehouse != self.transfer.to_warehouse:
            raise ValidationError("To inventory warehouse must match transfer's to warehouse.")
    
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
    
    # Fields to ensure immutability after processing
    is_locked = models.BooleanField(default=False, help_text="Indicates if the return record is locked and immutable after processing")
    locked_at = models.DateTimeField(null=True, blank=True, help_text="When the record was locked for immutability")
    original_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Original total amount before any changes (for audit purposes)")

    def __str__(self):
        return f"{self.return_type.title()} {self.return_number}"
    
    def clean(self):
        if self.total_amount < 0:
            raise ValidationError("Total amount cannot be negative.")
        if self.refund_amount < 0:
            raise ValidationError("Refund amount cannot be negative.")
        if self.refund_amount > self.total_amount:
            raise ValidationError("Refund amount cannot exceed total amount.")
        
        # Prevent changes to locked returns
        if self.pk and self.is_locked:
            original_instance = Return.objects.get(pk=self.pk)
            # Only allow changes to status for processed returns
            if (self.total_amount != original_instance.total_amount or
                self.refund_amount != original_instance.refund_amount or
                self.return_type != original_instance.return_type or
                self.original_sale_id != original_instance.original_sale_id or
                self.reason != original_instance.reason):
                
                # Create audit log for attempted unauthorized change
                from .signals import get_current_user
                current_user = get_current_user()
                
                AuditLog.objects.create(
                    user=current_user,
                    action='attempted_modification',
                    object_type='return',
                    object_id=self.pk,
                    object_repr=f'Return {self.return_number} (locked)',
                    old_values={
                        'total_amount': float(original_instance.total_amount),
                        'refund_amount': float(original_instance.refund_amount),
                        'reason': original_instance.reason,
                    },
                    new_values={
                        'total_amount': float(self.total_amount),
                        'refund_amount': float(self.refund_amount),
                        'reason': self.reason,
                    },
                    timestamp=timezone.now(),
                    notes='Attempted modification of locked return record'
                )
                
                raise ValidationError("Cannot modify a locked return record after processing.")
    
    def save(self, *args, **kwargs):
        # Store the old status to detect status changes
        old_status = None
        if self.pk:  # If this is an existing object
            old_return = Return.objects.get(pk=self.pk)
            old_status = old_return.status
        
        # Set original total for new returns
        if not self.original_total:
            self.original_total = self.total_amount
        
        # Lock the return record if it's processed to ensure immutability
        if self.status == 'processed' and not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
            # Store the original total to ensure audit trail
            if not self.original_total:
                self.original_total = self.total_amount
        
        self.clean()
        if not self.return_number:
            import uuid
            self.return_number = f"RET-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
        
        # Handle return processing based on status changes
        if old_status and old_status != self.status:
            if old_status == 'approved' and self.status == 'processed':
                self.process_return()
            elif old_status == 'pending' and self.status == 'rejected':
                # No action needed for rejection
                pass
    
    def process_return(self):
        """
        Process the return by restocking items and issuing refund/store credit
        """
        from django.db import transaction
        with transaction.atomic():
            # Process each return line
            for line in self.lines.all():
                # Get the warehouse associated with the original sale
                original_warehouse = self.original_sale.warehouse
                
                # Get the inventory record for this product in the original warehouse
                inventory, created = Inventory.objects.get_or_create(
                    product=line.product,
                    variant=line.variant,
                    warehouse=original_warehouse,
                    defaults={
                        'qty_on_hand': 0,
                        'qty_reserved': 0,
                        'min_stock_level': 0
                    }
                )
                
                # Add the returned quantity back to inventory
                if self.return_type == 'exchange':
                    # For exchanges, we may want to handle the new product differently
                    # For now, we add the returned items back to inventory
                    inventory.qty_on_hand += line.quantity
                else:
                    # For returns, add the items back to inventory
                    inventory.qty_on_hand += line.quantity
                
                inventory.save()
                
                # Mark the return line as processed
                line.is_returned = True
                line.save()
            
            # Process refund if applicable
            if self.return_type in ['return', 'refund'] and self.refund_amount > 0:
                self.issue_refund()
            
            # Update return status to processed
            self.processed_at = timezone.now()
            self.status = 'processed'
            self.save()
    
    def issue_refund(self):
        """
        Issue a refund based on the refund method specified
        """
        if self.refund_amount <= 0:
            return
            
        # Find the original payment for this amount to determine the payment method
        original_payments = self.original_sale.payments.all()
        
        # For simplicity, we'll create a refund record
        # In a real system, you might need to process actual refunds through payment processors
        from django.db import transaction
        with transaction.atomic():
            # For now, just mark the refund as processed
            self.refunded_at = timezone.now()
            self.save()
    
    def issue_store_credit(self, credit_amount=None):
        """
        Issue store credit to the customer
        """
        if not self.customer:
            raise ValidationError("Cannot issue store credit without a customer.")
        
        credit_amount = credit_amount or self.refund_amount
        
        if credit_amount <= 0:
            return
        
        from django.db import transaction
        with transaction.atomic():
            # Add credit to customer's store credit balance
            self.customer.store_credit += credit_amount
            self.customer.save()
            
            # Create a payment record indicating store credit was issued
            Payment.objects.create(
                sale=self.original_sale,
                payment_method='credit',
                amount=-credit_amount,  # Negative indicates credit
                reference=f"Store credit issued for return {self.return_number}"
            )
            
            # Update return record
            self.refund_amount = 0  # Since we're using store credit instead
            self.refunded_at = timezone.now()
            self.save()
    
    def restock_items(self, warehouse=None, location=None, bin=None, restock_type='normal'):
        """
        Restock returned items to specified location
        restock_type can be 'normal', 'quality_control', etc.
        """
        from django.db import transaction
        with transaction.atomic():
            for line in self.lines.all():
                # Use provided warehouse or default to original sale warehouse
                target_warehouse = warehouse or self.original_sale.warehouse
                
                # Create or get inventory record
                inventory, created = Inventory.objects.get_or_create(
                    product=line.product,
                    variant=line.variant,
                    warehouse=target_warehouse,
                    location=location,
                    bin=bin,
                    defaults={
                        'qty_on_hand': 0,
                        'qty_reserved': 0,
                        'min_stock_level': 0
                    }
                )
                
                # Add returned quantity to inventory based on restock type
                if restock_type == 'quality_control':
                    # In a real system, you might separate QC items
                    # For now, we'll add them to regular inventory
                    inventory.qty_on_hand += line.quantity
                else:
                    inventory.qty_on_hand += line.quantity
                
                inventory.save()
    
    def process_exchange(self, new_items_data):
        """
        Process an exchange by creating a new sale with exchange items
        """
        from django.db import transaction
        with transaction.atomic():
            # Create a new sale for the exchanged items
            import uuid
            new_sale = Sale.objects.create(
                receipt_number=f"EXC-{uuid.uuid4().hex[:8].upper()}",
                cashier=self.original_sale.cashier,
                customer=self.original_sale.customer,
                warehouse=self.original_sale.warehouse,
                total_amount=0,  # Will be calculated based on new items
                sale_type='exchange',
                payment_status='completed'  # Exchange completed
            )
            
            total_amount = 0
            for item_data in new_items_data:
                product = Product.objects.get(id=item_data['product_id'])
                variant = ProductVariant.objects.get(id=item_data['variant_id']) if item_data.get('variant_id') else None
                
                # Create sale line for new item
                sale_line = SaleLine.objects.create(
                    sale=new_sale,
                    product=product,
                    variant=variant,
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    total_price=item_data['quantity'] * item_data['unit_price']
                )
                
                total_amount += sale_line.total_price
                
                # Update inventory for the new items (decrease stock)
                inventory = Inventory.objects.get(
                    product=product,
                    variant=variant,
                    warehouse=self.original_sale.warehouse
                )
                inventory.qty_on_hand -= item_data['quantity']
                inventory.save()
            
            # Update the new sale with calculated total
            new_sale.total_amount = total_amount
            new_sale.save()
            
            # Create payment record for the exchange transaction
            exchange_payment_amount = total_amount - self.refund_amount  # Net amount after refund
            if exchange_payment_amount > 0:
                # Customer pays difference
                Payment.objects.create(
                    sale=new_sale,
                    payment_method='cash',  # Could be configurable
                    amount=exchange_payment_amount
                )
            elif exchange_payment_amount < 0:
                # Store owes customer (would require store credit system)
                # For now, we just note it in our records
                pass
            
            return new_sale


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
    
    def is_eligible_for_customer(self, customer_user=None):
        """
        Check if a customer is eligible for this promotion based on customer groups
        """
        if not self.customer_groups.exists():
            # If no customer groups are specified, all customers are eligible
            return True
        
        if not customer_user:
            # If no user is provided, we can't check group eligibility
            return False
        
        # Get customer's user groups
        user_groups = set(customer_user.groups.all())
        promotion_groups = set(self.customer_groups.all())
        
        # Check if user belongs to any of the required groups
        return bool(user_groups.intersection(promotion_groups))
    
    def calculate_discount(self, product, customer_user=None, quantity=1, unit_price=None):
        """
        Calculate the discount amount for a specific product and quantity
        """
        if not self.is_valid() or not self.is_eligible_for_customer(customer_user):
            return 0
        
        # Check if product is eligible for promotion
        if (self.products.exists() and product not in self.products.all()):
            # If promotion has specific products and this product is not included
            return 0
        
        # Check if any of the product's categories are eligible
        if (self.categories.exists() and 
            product.category and 
            product.category not in self.categories.all()):
            # If promotion has specific categories and product's category is not included
            return 0
        
        if unit_price is None:
            unit_price = product.price
        
        total_price = unit_price * quantity
        
        if self.promotion_type == 'percentage':
            # Apply percentage discount
            discount_amount = total_price * (self.discount_value / 100)
        elif self.promotion_type == 'fixed_amount':
            # Apply fixed amount discount (capped at total price)
            discount_amount = min(self.discount_value, total_price)
        elif self.promotion_type == 'buy_x_get_y':
            # For Buy X Get Y promotions
            if self.buy_quantity and self.get_quantity:
                # Calculate how many free items customer gets
                qualifying_groups = quantity // (self.buy_quantity + self.get_quantity)
                free_items = qualifying_groups * self.get_quantity
                discount_amount = free_items * unit_price
            else:
                discount_amount = 0
        else:
            discount_amount = 0
        
        return discount_amount
    
    def apply_to_product_price(self, product, customer_user=None, quantity=1, original_price=None):
        """
        Apply the promotion to a product and return the discounted price
        """
        if original_price is None:
            original_price = product.price
        
        discount = self.calculate_discount(product, customer_user, quantity, original_price)
        discounted_price = original_price - (discount / quantity)  # Discount per item
        
        return max(discounted_price, 0)  # Ensure price doesn't go negative
    
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
    destination_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True,
                                           help_text="Destination location within warehouse (optional)")
    destination_bin = models.ForeignKey(Bin, on_delete=models.SET_NULL, null=True, blank=True,
                                       help_text="Destination bin within location (optional)")
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
        # Validate location/warehouse consistency
        if self.destination_location and self.destination_location.warehouse != self.warehouse:
            raise ValidationError("Destination location must belong to the selected warehouse.")
        # Validate bin/location consistency
        if self.destination_bin and self.destination_bin.location != self.destination_location:
            raise ValidationError("Destination bin must belong to the selected location.")
    
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
    destination_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True,
                                           help_text="Destination location for this item (optional)")
    destination_bin = models.ForeignKey(Bin, on_delete=models.SET_NULL, null=True, blank=True,
                                       help_text="Destination bin for this item (optional)")
    
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
        # Validate location/warehouse consistency
        if self.destination_location and self.destination_location.warehouse != self.purchase_order.warehouse:
            raise ValidationError("Destination location must belong to the purchase order's warehouse.")
        # Validate bin/location consistency
        if self.destination_bin and self.destination_bin.location != self.destination_location:
            raise ValidationError("Destination bin must belong to the selected location.")
    
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
    destination_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True,
                                           help_text="Specific destination location for this received item (optional)")
    destination_bin = models.ForeignKey(Bin, on_delete=models.SET_NULL, null=True, blank=True,
                                       help_text="Specific destination bin for this received item (optional)")

    def __str__(self):
        return f"{self.received_qty}x {self.purchase_order_line.product.name} (GRN: {self.grn.grn_number})"

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    reservation_number = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Reservation {self.reservation_number}"

    def clean(self):
        if self.expires_at <= timezone.now():
            raise ValidationError("Expiration date must be in the future.")

    def save(self, *args, **kwargs):
        if not self.reservation_number:
            self.reservation_number = f"RES-{uuid.uuid4().hex[:8].upper()}"
        self.clean()
        super().save(*args, **kwargs)

class ReservationLine(models.Model):
    reservation = models.ForeignKey(Reservation, related_name='lines', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        variant_str = f" - {self.variant.name}" if self.variant else ""
        return f"{self.quantity}x {self.product.name}{variant_str}"

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class BlacklistedToken(models.Model):
    """Model to store blacklisted JWT tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    jti = models.CharField(max_length=255, unique=True)  # JWT ID
    token = models.TextField()  # Full token (optional, for debugging)
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    reason = models.CharField(max_length=100, blank=True, help_text="Reason for blacklisting")

    def __str__(self):
        return f"Blacklisted Token for {self.user.username if self.user else 'Unknown'} - {self.jti[:10]}..."

    class Meta:
        ordering = ['-blacklisted_at']


class Webhook(models.Model):
    """
    Model to store webhook configurations
    """
    EVENT_CHOICES = [
        ('sale_completed', 'Sale Completed'),
        ('stock_level_changed', 'Stock Level Changed'),
        ('customer_created', 'Customer Created'),
        ('inventory_updated', 'Inventory Updated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Name/description for this webhook")
    target_url = models.URLField(help_text="The URL to send the webhook payload to")
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES, help_text="Type of event that triggers this webhook")
    is_active = models.BooleanField(default=True, help_text="Whether this webhook is currently active")
    secret = models.CharField(max_length=255, blank=True, help_text="Secret key for webhook signature verification")
    headers = models.JSONField(default=dict, blank=True, help_text="Additional headers to send with webhook")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_triggered = models.DateTimeField(null=True, blank=True, help_text="When this webhook was last triggered")
    
    def __str__(self):
        return f"{self.name} - {self.target_url} ({self.event_type})"

    class Meta:
        ordering = ['-created_at']


class WebhookLog(models.Model):
    """
    Model to store webhook delivery logs
    """
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name='logs')
    payload = models.JSONField(help_text="The JSON payload sent to the webhook")
    response_status = models.IntegerField(null=True, blank=True, help_text="HTTP status code from webhook response")
    response_content = models.TextField(blank=True, help_text="Response content from webhook")
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"Webhook Log: {self.webhook.name} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']


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


# Payment Gateway Integration
class PaymentToken(models.Model):
    """
    Model to store payment tokens from payment gateways (Stripe, PayPal, etc.)
    """
    PAYMENT_GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('square', 'Square'),
        ('razorpay', 'Razorpay'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payment_tokens')
    token = models.CharField(max_length=255, unique=True, help_text="Token from payment gateway")
    gateway = models.CharField(max_length=20, choices=PAYMENT_GATEWAY_CHOICES, help_text="Payment gateway provider")
    masked_card_number = models.CharField(max_length=20, blank=True, help_text="Masked card number for display")
    expiry_month = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Card expiry month")
    expiry_year = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Card expiry year")
    card_brand = models.CharField(max_length=20, blank=True, help_text="Card brand (Visa, Mastercard, etc.)")
    is_default = models.BooleanField(default=False, help_text="Whether this is the customer's default payment method")
    is_active = models.BooleanField(default=True, help_text="Whether this token is still valid")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.customer.first_name} {self.customer.last_name} - {self.gateway} Token"
    
    class Meta:
        unique_together = ['customer', 'token']
        ordering = ['-created_at']


class PaymentGatewayConfig(models.Model):
    """
    Model to store payment gateway configuration
    """
    GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    ]
    
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES, unique=True)
    public_key = models.CharField(max_length=255, help_text="Public/API key for the gateway")
    secret_key = models.CharField(max_length=255, help_text="Secret key for the gateway")
    webhook_secret = models.CharField(max_length=255, blank=True, help_text="Webhook signing secret")
    is_sandbox = models.BooleanField(default=True, help_text="Whether to use sandbox/test environment")
    is_active = models.BooleanField(default=True, help_text="Whether this gateway is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.gateway.title()} Configuration"
    
    class Meta:
        verbose_name = "Payment Gateway Configuration"
        verbose_name_plural = "Payment Gateway Configurations"


class EcommercePlatform(models.Model):
    """
    Model to store e-commerce platform configurations
    """
    PLATFORM_CHOICES = [
        ('shopify', 'Shopify'),
        ('woocommerce', 'WooCommerce'),
        ('magento', 'Magento'),
        ('bigcommerce', 'BigCommerce'),
        ('custom', 'Custom API'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, help_text="Name of the e-commerce integration")
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, help_text="E-commerce platform type")
    api_url = models.URLField(help_text="Base API URL for the e-commerce platform")
    api_key = models.CharField(max_length=255, help_text="API key for authentication")
    api_secret = models.CharField(max_length=255, help_text="API secret for authentication")
    additional_config = models.JSONField(default=dict, blank=True, help_text="Additional configuration parameters")
    is_active = models.BooleanField(default=True, help_text="Whether this integration is active")
    sync_products = models.BooleanField(default=True, help_text="Whether to sync products from POS to e-commerce")
    sync_inventory = models.BooleanField(default=True, help_text="Whether to sync inventory from POS to e-commerce")
    sync_orders = models.BooleanField(default=True, help_text="Whether to sync orders from e-commerce to POS")
    last_sync = models.DateTimeField(null=True, blank=True, help_text="Last successful sync timestamp")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.platform.title()} - {self.name}"
    
    class Meta:
        verbose_name = "E-commerce Platform"
        verbose_name_plural = "E-commerce Platforms"


class EcommerceSyncLog(models.Model):
    """
    Model to track e-commerce sync operations
    """
    SYNC_TYPE_CHOICES = [
        ('product', 'Product Sync'),
        ('inventory', 'Inventory Sync'),
        ('order', 'Order Sync'),
        ('customer', 'Customer Sync'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    platform = models.ForeignKey(EcommercePlatform, on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES, help_text="Type of sync operation")
    status = models.CharField(max_length=20, choices=[
        ('started', 'Started'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ])
    records_synced = models.IntegerField(default=0, help_text="Number of records successfully synced")
    total_records = models.IntegerField(default=0, help_text="Total number of records processed")
    error_message = models.TextField(blank=True, help_text="Error message if sync failed")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.platform.name} - {self.sync_type} - {self.status}"
    
    class Meta:
        ordering = ['-started_at']


# Signal handlers for webhooks
@receiver(post_save, sender=Sale)
def sale_post_save(sender, instance, created, **kwargs):
    """
    Trigger webhook when a sale is completed (payment_status changes to 'completed')
    """
    if not created and hasattr(instance, 'original_payment_status'):
        # Check if payment status changed to completed
        if instance.original_payment_status != 'completed' and instance.payment_status == 'completed':
            trigger_sale_completed_webhooks(instance)


@receiver(pre_save, sender=Sale)
def sale_pre_save(sender, instance, **kwargs):
    """
    Store the original payment status before saving
    """
    if instance.pk:
        try:
            original = Sale.objects.get(pk=instance.pk)
            instance.original_payment_status = original.payment_status
        except Sale.DoesNotExist:
            instance.original_payment_status = None
    else:
        instance.original_payment_status = None


@receiver(post_save, sender=Inventory)
def inventory_post_save(sender, instance, created, **kwargs):
    """
    Trigger webhook when inventory quantity changes
    """
    if not created and hasattr(instance, 'original_qty_on_hand'):
        # Check if quantity changed
        if instance.original_qty_on_hand != instance.qty_on_hand:
            # Import here to avoid circular import issues
            from .services import trigger_stock_level_changed_webhooks
            trigger_stock_level_changed_webhooks(
                instance, 
                instance.original_qty_on_hand, 
                instance.qty_on_hand
            )


@receiver(pre_save, sender=Inventory)
def inventory_pre_save(sender, instance, **kwargs):
    """
    Store the original quantity on hand before saving
    """
    if instance.pk:
        try:
            original = Inventory.objects.get(pk=instance.pk)
            instance.original_qty_on_hand = original.qty_on_hand
        except Inventory.DoesNotExist:
            instance.original_qty_on_hand = None
    else:
        instance.original_qty_on_hand = None