# pos_app/signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import (
    Product, Sale, Inventory, Warehouse, Customer, UserProfile,
    Transfer, Return, AuditLog
)
import logging
from django.utils import timezone
from django.contrib.auth.models import User as DjangoUser
from threading import local

logger = logging.getLogger(__name__)

# Thread-local storage for request context
_thread_locals = local()

def set_current_user(user):
    """Set the current user in thread-local storage"""
    _thread_locals.user = user

def get_current_user():
    """Get the current user from thread-local storage"""
    return getattr(_thread_locals, 'user', None)

# pre_save signals to capture old values
@receiver(pre_save, sender=Warehouse)
def warehouse_pre_save(sender, instance, **kwargs):
    if instance.pk: # Only for existing instances
        try:
            original_warehouse = Warehouse.objects.get(pk=instance.pk)
            instance._original_location = original_warehouse.location
        except Warehouse.DoesNotExist:
            instance._original_location = None

@receiver(pre_save, sender=Product)
def product_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._original_values = Product.objects.values('name', 'sku', 'price', 'cost_price').get(pk=instance.pk)
        except Product.DoesNotExist:
            instance._original_values = {}

@receiver(pre_save, sender=Sale)
def sale_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Sale.objects.get(pk=instance.pk)
            instance._audit_old_values = {
                'receipt_number': old_instance.receipt_number,
                'total_amount': float(old_instance.total_amount),
                'payment_status': old_instance.payment_status,
                'sale_date': old_instance.sale_date.isoformat() if old_instance.sale_date else None,
            }
        except Sale.DoesNotExist:
            instance._audit_old_values = None

@receiver(pre_save, sender=Inventory)
def inventory_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Inventory.objects.get(pk=instance.pk)
            instance._audit_old_values = {
                'qty_on_hand': old_instance.qty_on_hand,
                'qty_reserved': old_instance.qty_reserved,
                'last_updated': old_instance.last_updated.isoformat() if old_instance.last_updated else None,
            }
        except Inventory.DoesNotExist:
            instance._audit_old_values = None

@receiver(pre_save, sender=Customer)
def customer_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Customer.objects.get(pk=instance.pk)
            instance._audit_old_values = {
                'first_name': old_instance.first_name,
                'last_name': old_instance.last_name,
                'email': old_instance.email,
                'phone': old_instance.phone,
                'loyalty_points': old_instance.loyalty_points,
            }
        except Customer.DoesNotExist:
            instance._audit_old_values = None

@receiver(pre_save, sender=Transfer)
def transfer_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Transfer.objects.get(pk=instance.pk)
            instance._audit_old_values = {
                'status': old_instance.status,
                'transfer_number': old_instance.transfer_number,
            }
        except Transfer.DoesNotExist:
            instance._audit_old_values = None

@receiver(pre_save, sender=Return)
def return_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Return.objects.get(pk=instance.pk)
            instance._audit_old_values = {
                'status': old_instance.status,
                'return_number': old_instance.return_number,
                'total_amount': float(old_instance.total_amount),
            }
        except Return.DoesNotExist:
            instance._audit_old_values = None


# post_save and post_delete signals for websockets and audit logs
@receiver(post_save, sender=Product)
def product_saved(sender, instance, created, **kwargs):
    """
    Send WebSocket message and create audit log when a product is saved.
    """
    try:
        # WebSocket message
        channel_layer = get_channel_layer()
        action = 'create' if created else 'update'
        product_data = {
            'id': instance.id, 'name': instance.name, 'sku': instance.sku,
            'barcode': instance.barcode, 'description': instance.description,
            'category': instance.category.id if instance.category else None,
            'price': float(instance.price),
            'cost_price': float(instance.cost_price) if instance.cost_price else None,
        }
        async_to_sync(channel_layer.group_send)(
            "products",
            {"type": "product_update_message", "product": product_data, "action": action}
        )

        # Audit logging
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        
        old_values = {}
        if not created:
            old_values = getattr(instance, '_original_values', {})
        
        new_values = {
            'name': instance.name, 'sku': instance.sku, 'price': float(instance.price),
            'cost_price': float(instance.cost_price) if instance.cost_price else None,
        }

        AuditLog.objects.create(
            user=audit_user, action=action, object_type='product', object_id=instance.pk,
            object_repr=f'Product {instance.name} (SKU: {instance.sku})',
            old_values=old_values, new_values=new_values, timestamp=timezone.now(),
            notes=f"Product {action} via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error in product_saved signal: {e}")

@receiver(post_delete, sender=Product)
def product_deleted(sender, instance, **kwargs):
    """
    Send WebSocket message and create audit log when a product is deleted.
    """
    try:
        # WebSocket message
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "products",
            {"type": "product_update_message", "productId": instance.id, "action": "delete"}
        )

        # Audit log
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        AuditLog.objects.create(
            user=audit_user, action='delete', object_type='product', object_id=instance.pk,
            object_repr=f'Product {instance.name} (SKU: {instance.sku})',
            old_values={
                'name': instance.name, 'sku': instance.sku, 'price': float(instance.price),
                'cost_price': float(instance.cost_price) if instance.cost_price else None,
            },
            timestamp=timezone.now(),
            notes=f"Product deleted via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error in product_deleted signal: {e}")

@receiver(post_save, sender=Sale)
def sale_saved(sender, instance, created, **kwargs):
    """
    Send WebSocket message and create audit log when a sale is saved.
    """
    try:
        # WebSocket message
        channel_layer = get_channel_layer()
        action = 'create' if created else 'update'
        sale_data = {
            'id': instance.id, 'receipt_number': instance.receipt_number,
            'cashier': instance.cashier.id,
            'customer': instance.customer.id if instance.customer else None,
            'warehouse': instance.warehouse.id,
            'total_amount': float(instance.total_amount),
            'tax_amount': float(instance.tax_amount),
            'discount_amount': float(instance.discount_amount),
            'payment_status': instance.payment_status,
            'sale_date': instance.sale_date.isoformat(),
        }
        async_to_sync(channel_layer.group_send)(
            "sales",
            {"type": "sale_update_message", "sale": sale_data, "action": action}
        )

        # Audit logging
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        old_values = {}
        if not created:
            old_values = getattr(instance, '_audit_old_values', {})

        new_values = {
            'receipt_number': instance.receipt_number,
            'total_amount': float(instance.total_amount),
            'payment_status': instance.payment_status,
        }
        AuditLog.objects.create(
            user=audit_user, action=action, object_type='sale', object_id=instance.pk,
            object_repr=f'Sale {instance.receipt_number}',
            old_values=old_values, new_values=new_values, timestamp=timezone.now(),
            notes=f"Sale {action} via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error in sale_saved signal: {e}")

@receiver(post_delete, sender=Sale)
def sale_deleted(sender, instance, **kwargs):
    """
    Send WebSocket message and create audit log when a sale is deleted.
    """
    try:
        # WebSocket message
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "sales",
            {"type": "sale_update_message", "saleId": instance.id, "action": "delete"}
        )

        # Audit log
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        AuditLog.objects.create(
            user=audit_user, action='delete', object_type='sale', object_id=instance.pk,
            object_repr=f'Sale {instance.receipt_number}',
            old_values={
                'receipt_number': instance.receipt_number,
                'total_amount': float(instance.total_amount),
            },
            timestamp=timezone.now(),
            notes=f"Sale deleted via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error in sale_deleted signal: {e}")

@receiver(post_save, sender=Inventory)
def inventory_saved(sender, instance, created, **kwargs):
    """
    Send WebSocket message and create audit log when inventory is saved.
    """
    try:
        # WebSocket message
        channel_layer = get_channel_layer()
        action = 'create' if created else 'update'
        inventory_data = {
            'id': instance.id, 'product': instance.product.id,
            'variant': instance.variant.id if instance.variant else None,
            'warehouse': instance.warehouse.id, 'qty_on_hand': instance.qty_on_hand,
            'qty_reserved': instance.qty_reserved, 'min_stock_level': instance.min_stock_level,
            'last_updated': instance.last_updated.isoformat(),
        }
        async_to_sync(channel_layer.group_send)(
            "inventory",
            {"type": "inventory_update_message", "inventory": inventory_data, "action": action}
        )

        # Audit logging
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        old_values = {}
        if not created:
            old_values = getattr(instance, '_audit_old_values', {})
        
        new_values = {
            'qty_on_hand': instance.qty_on_hand,
            'qty_reserved': instance.qty_reserved,
            'min_stock_level': instance.min_stock_level,
        }
        AuditLog.objects.create(
            user=audit_user, action=action, object_type='inventory', object_id=instance.pk,
            object_repr=f'Inventory for {instance.product.name}',
            old_values=old_values, new_values=new_values, timestamp=timezone.now(),
            notes=f"Inventory {action} via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error in inventory_saved signal: {e}")

@receiver(post_delete, sender=Inventory)
def inventory_deleted(sender, instance, **kwargs):
    """
    Send WebSocket message and create audit log when inventory is deleted.
    """
    try:
        # WebSocket message
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "inventory",
            {"type": "inventory_update_message", "inventoryId": instance.id, "action": "delete"}
        )

        # Audit log
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        AuditLog.objects.create(
            user=audit_user, action='delete', object_type='inventory', object_id=instance.pk,
            object_repr=f'Inventory for {instance.product.name}',
            old_values={
                'qty_on_hand': instance.qty_on_hand,
                'qty_reserved': instance.qty_reserved,
                'min_stock_level': instance.min_stock_level,
            },
            timestamp=timezone.now(),
            notes=f"Inventory deleted via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error in inventory_deleted signal: {e}")

@receiver(post_save, sender=Warehouse)
def warehouse_saved(sender, instance, created, **kwargs):
    """
    Send WebSocket message when a warehouse is saved.
    """
    try:
        channel_layer = get_channel_layer()
        action = 'create' if created else 'update'
        warehouse_data = {
            'id': instance.id, 'name': instance.name, 'location': instance.location,
            'contact_person': instance.contact_person, 'contact_phone': instance.contact_phone,
            'contact_email': instance.contact_email, 'capacity': instance.capacity,
            'is_active': instance.is_active,
            'created_at': instance.created_at.isoformat() if hasattr(instance, 'created_at') and instance.created_at else None,
        }
        async_to_sync(channel_layer.group_send)(
            "warehouses",
            {"type": "warehouse_update_message", "warehouse": warehouse_data, "action": action}
        )
    except Exception as e:
        logger.error(f"Error sending warehouse update via WebSocket: {e}")

@receiver(post_delete, sender=Warehouse)
def warehouse_deleted(sender, instance, **kwargs):
    """
    Send WebSocket message when a warehouse is deleted.
    """
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "warehouses",
            {"type": "warehouse_update_message", "warehouseId": instance.id, "action": "delete"}
        )
    except Exception as e:
        logger.error(f"Error sending warehouse delete via WebSocket: {e}")

@receiver(post_save, sender=Customer)
def customer_saved(sender, instance, created, **kwargs):
    """
    Create audit log when a customer is saved.
    """
    try:
        # Audit logging
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        action = 'create' if created else 'update'
        old_values = getattr(instance, '_audit_old_values', None)
        
        new_values = {
            'first_name': instance.first_name, 'last_name': instance.last_name,
            'email': instance.email, 'phone': instance.phone,
            'loyalty_points': instance.loyalty_points,
        }
        
        AuditLog.objects.create(
            user=audit_user, action=action, object_type='customer', object_id=instance.id,
            object_repr=f"Customer: {instance.first_name} {instance.last_name}",
            old_values=old_values, new_values=new_values, timestamp=timezone.now(),
            notes=f"Customer {action} via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error creating customer audit log: {e}")

@receiver(post_delete, sender=Customer)
def customer_deleted(sender, instance, **kwargs):
    """
    Create audit log when a customer is deleted.
    """
    try:
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        old_values = {
            'first_name': instance.first_name, 'last_name': instance.last_name,
            'email': instance.email, 'phone': instance.phone,
            'loyalty_points': instance.loyalty_points,
        }
        
        AuditLog.objects.create(
            user=audit_user, action='delete', object_type='customer', object_id=instance.id,
            object_repr=f"Customer: {instance.first_name} {instance.last_name}",
            old_values=old_values, new_values=None, timestamp=timezone.now(),
            notes=f"Customer delete via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error creating customer delete audit log: {e}")

@receiver(post_save, sender=Transfer)
def transfer_saved(sender, instance, created, **kwargs):
    """
    Create audit log when a transfer is saved.
    """
    try:
        # Audit logging
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        action = 'create' if created else 'update'
        old_values = getattr(instance, '_audit_old_values', None)
        
        new_values = {
            'status': instance.status,
            'transfer_number': instance.transfer_number,
        }
        
        AuditLog.objects.create(
            user=audit_user, action=action, object_type='transfer', object_id=instance.id,
            object_repr=f"Transfer: {instance.transfer_number}",
            old_values=old_values, new_values=new_values, timestamp=timezone.now(),
            notes=f"Transfer {action} via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error creating transfer audit log: {e}")

@receiver(post_delete, sender=Transfer)
def transfer_deleted(sender, instance, **kwargs):
    """
    Create audit log when a transfer is deleted.
    """
    try:
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        old_values = {
            'status': instance.status,
            'transfer_number': instance.transfer_number,
        }
        
        AuditLog.objects.create(
            user=audit_user, action='delete', object_type='transfer', object_id=instance.id,
            object_repr=f"Transfer: {instance.transfer_number}",
            old_values=old_values, new_values=None, timestamp=timezone.now(),
            notes=f"Transfer delete via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error creating transfer delete audit log: {e}")

@receiver(post_save, sender=Return)
def return_saved(sender, instance, created, **kwargs):
    """
    Create audit log when a return is saved.
    """
    try:
        # Audit logging
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        action = 'create' if created else 'update'
        old_values = getattr(instance, '_audit_old_values', None)
        
        new_values = {
            'status': instance.status,
            'return_number': instance.return_number,
            'total_amount': float(instance.total_amount),
        }
        
        AuditLog.objects.create(
            user=audit_user, action=action, object_type='return', object_id=instance.id,
            object_repr=f"Return: {instance.return_number}",
            old_values=old_values, new_values=new_values, timestamp=timezone.now(),
            notes=f"Return {action} via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error creating return audit log: {e}")

@receiver(post_delete, sender=Return)
def return_deleted(sender, instance, **kwargs):
    """
    Create audit log when a return is deleted.
    """
    try:
        # Audit log
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        old_values = {
            'status': instance.status,
            'return_number': instance.return_number,
            'total_amount': float(instance.total_amount),
        }
        
        AuditLog.objects.create(
            user=audit_user, action='delete', object_type='return', object_id=instance.id,
            object_repr=f"Return: {instance.return_number}",
            old_values=old_values, new_values=None, timestamp=timezone.now(),
            notes=f"Return delete via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error creating return delete audit log: {e}")

@receiver(post_save, sender=DjangoUser)
def user_saved(sender, instance, created, **kwargs):
    """
    Create audit log when a user is saved.
    """
    try:
        # Audit logging
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        action = 'create' if created else 'update'
        
        new_values = {
            'username': instance.username, 'email': instance.email,
            'first_name': instance.first_name, 'last_name': instance.last_name,
            'is_active': instance.is_active,
        }
        
        AuditLog.objects.create(
            user=audit_user, action=action, object_type='user', object_id=instance.pk,
            object_repr=f'User {instance.username}',
            new_values=new_values, timestamp=timezone.now(),
            notes=f"User {action} via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error creating user audit log: {e}")

@receiver(post_delete, sender=DjangoUser)
def user_deleted(sender, instance, **kwargs):
    """
    Create audit log when a user is deleted.
    """
    try:
        # Audit logging
        user = get_current_user()
        audit_user = user if user and user.is_authenticated else None # Assign None if anonymous
        AuditLog.objects.create(
            user=audit_user, action='delete', object_type='user', object_id=instance.pk,
            object_repr=f'User {instance.username}',
            old_values={'username': instance.username, 'email': instance.email},
            timestamp=timezone.now(),
            notes=f"User deleted via {'admin' if user and user.is_staff else 'API' if user else 'system'}"
        )
    except Exception as e:
        logger.error(f"Error creating user audit log: {e}")

@receiver(post_save, sender=Warehouse)
def create_default_location_for_warehouse(sender, instance, created, **kwargs):
    """
    Automatically creates a default Location for a new Warehouse,
    or ensures one exists when an existing Warehouse is saved.
    """
    # This logic applies to both new and existing warehouses
    from .models import Location
    from django.db import transaction
    try:
        # Use get_or_create to prevent race conditions when creating default location
        with transaction.atomic():
            Location.objects.get_or_create(
                warehouse=instance,
                code="DEFAULT",
                defaults={
                    'name': f"Default Location for {instance.name}",
                    'description': "Automatically created default location"
                }
            )

        # Update associated Location names if Warehouse.location has changed
        if not created and hasattr(instance, '_original_location') and instance._original_location != instance.location:
            # Update all locations associated with this warehouse (except the default one just created/updated)
            Location.objects.filter(warehouse=instance).exclude(code="DEFAULT").update(name=instance.location)
            logger.info(f"Updated Location names for warehouse {instance.name} to: {instance.location}")

    except Exception as e:
        logger.error(f"Error in warehouse post_save signal for {instance.name}: {e}")
