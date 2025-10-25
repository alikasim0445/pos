"""
Test script to verify the reservation & allocation implementation meets all requirements:
FR-21: Reserve stock for pending sales/orders.
FR-22: Release or reassign reservations when orders are canceled.
"""
import os
import django
from django.conf import settings
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_project.settings')
django.setup()

from pos_app.models import (
    Warehouse, Product, ProductVariant, Inventory, 
    UserProfile, User, Sale, SaleLine
)
from django.contrib.auth.models import User as DjangoUser
from django.core.exceptions import ValidationError


def test_reservation_allocation():
    print("Testing Reservation & Allocation Implementation...")
    
    # Generate unique suffix for this test run
    timestamp_suffix = timezone.now().strftime("%Y%m%d%H%M%S")
    
    # Test FR-21: Reserve stock for pending sales/orders
    print("\n1. Testing Stock Reservation for Pending Sales...")
    
    # Create warehouse
    warehouse = Warehouse.objects.create(
        name=f"Test Warehouse {timestamp_suffix}",
        location="123 Test St, City",
        warehouse_type="warehouse",
        contact_person="John Doe",
        contact_phone="555-1234",
        contact_email="test@example.com",
        capacity=10000
    )
    print(f"   Created warehouse: {warehouse.name}")
    
    # Create products
    product = Product.objects.create(
        name=f"Test Product {timestamp_suffix}",
        sku=f"TEST-SP-{timestamp_suffix}",
        price=10.99
    )
    print(f"   Created product: {product.name}")
    
    # Create a user for the test
    test_user, created = User.objects.get_or_create(
        username=f"test_cashier_{timestamp_suffix}",
        defaults={'email': f'cashier_{timestamp_suffix}@example.com', 'is_active': True}
    )
    if created:
        test_user.set_password('password123')
        test_user.save()
    print(f"   Created cashier user: {test_user.username}")
    
    # Create inventory at the warehouse
    inventory = Inventory.objects.create(
        product=product,
        warehouse=warehouse,
        qty_on_hand=100,  # 100 units available
        qty_reserved=0,
        min_stock_level=20
    )
    print(f"   Created inventory: {inventory.qty_on_hand} units on hand, {inventory.qty_reserved} reserved")
    
    # Create a pending sale with items that require stock reservation
    sale = Sale.objects.create(
        receipt_number=f"RCP-{timestamp_suffix}-001",
        cashier=test_user,
        warehouse=warehouse,
        total_amount=21.98,  # 2 items * $10.99
        payment_status='pending',  # Start with pending status to trigger reservation
        notes="Test sale for reservation"
    )
    
    # Create sale lines
    sale_line = SaleLine.objects.create(
        sale=sale,
        product=product,
        quantity=2,
        unit_price=10.99,
        total_price=21.98
    )
    print(f"   Created pending sale: {sale.receipt_number} with {sale_line.quantity} units")
    
    # Refresh inventory from DB to see if auto-reservation worked
    inventory.refresh_from_db()
    print(f"   Inventory after pending sale: {inventory.qty_on_hand} on hand, {inventory.qty_reserved} reserved")
    
    # Check if stock was automatically reserved
    if inventory.qty_reserved == 2:
        print("   ✓ Stock automatically reserved when pending sale was created")
    else:
        print(f"   ✗ Expected 2 reserved, but got {inventory.qty_reserved}")
    
    # Test FR-22: Release reservations when orders are canceled
    print("\n2. Testing Stock Release for Canceled Sales...")
    
    print(f"   Inventory before cancellation: {inventory.qty_on_hand} on hand, {inventory.qty_reserved} reserved")
    
    # Change the sale status to cancelled
    sale.payment_status = 'cancelled'
    sale.save()
    
    # Refresh inventory from DB to see if stock was released
    inventory.refresh_from_db()
    print(f"   Inventory after cancellation: {inventory.qty_on_hand} on hand, {inventory.qty_reserved} reserved")
    
    # Check if stock was released
    if inventory.qty_reserved == 0:
        print("   ✓ Stock automatically released when sale was cancelled")
    else:
        print(f"   ✗ Expected 0 reserved after cancellation, but got {inventory.qty_reserved}")
    
    # Test creating another sale and completing it
    print("\n3. Testing Sale Completion...")
    
    # Create another sale
    completed_sale = Sale.objects.create(
        receipt_number=f"RCP-{timestamp_suffix}-002",
        cashier=test_user,
        warehouse=warehouse,
        total_amount=10.99,
        payment_status='pending',  # Start as pending
        notes="Test sale for completion"
    )
    
    completed_sale_line = SaleLine.objects.create(
        sale=completed_sale,
        product=product,
        quantity=1,
        unit_price=10.99,
        total_price=10.99
    )
    print(f"   Created pending sale: {completed_sale.receipt_number} with {completed_sale_line.quantity} units")
    
    # Check inventory after creating pending sale
    inventory.refresh_from_db()
    print(f"   Inventory after pending sale: {inventory.qty_on_hand} on hand, {inventory.qty_reserved} reserved")
    
    # Now complete the sale
    completed_sale.payment_status = 'completed'
    completed_sale.save()
    
    # Refresh inventory from DB to see if stock was reduced
    inventory.refresh_from_db()
    print(f"   Inventory after completion: {inventory.qty_on_hand} on hand, {inventory.qty_reserved} reserved")
    
    # Check if stock was properly reduced
    expected_on_hand = 100 - 2 - 1  # Original 100 - 2 from first sale - 1 from completed sale
    if inventory.qty_on_hand == expected_on_hand and inventory.qty_reserved == 0:
        print("   ✓ Stock properly reduced when sale was completed")
    else:
        print(f"   ✗ Expected {expected_on_hand} on hand and 0 reserved, got {inventory.qty_on_hand} on hand and {inventory.qty_reserved} reserved")
    
    # Test trying to create a sale with insufficient stock
    print("\n4. Testing Insufficient Stock Validation...")
    
    try:
        # Create a sale that would require more stock than available
        # Currently we have 97 on hand (100 - 2 - 1), 0 reserved
        large_sale = Sale.objects.create(
            receipt_number=f"RCP-{timestamp_suffix}-003",
            cashier=test_user,
            warehouse=warehouse,
            total_amount=109.90,  # 10 items * $10.99
            payment_status='pending',
            notes="Test sale with more items than available stock"
        )
        
        large_sale_line = SaleLine.objects.create(
            sale=large_sale,
            product=product,
            quantity=110,  # Try to reserve 110 units when only 97 are available
            unit_price=10.99,
            total_price=1208.90
        )
        
        # This should trigger reservation and fail with validation error
        large_sale.reserve_stock_for_sale()
        print("   ✗ Validation failed - sale with insufficient stock was allowed")
    except ValidationError as e:
        print(f"   ✓ Properly prevented sale with insufficient stock: {str(e)}")
    except Exception as e:
        print(f"   ? Other error occurred (might be expected): {str(e)}")
    
    print("\nAll reservation & allocation tests completed!")
    
    # Clean up
    print("\nCleaning up test data...")
    SaleLine.objects.filter(sale__receipt_number__contains=timestamp_suffix).delete()
    Sale.objects.filter(receipt_number__contains=timestamp_suffix).delete()
    Inventory.objects.filter(product=product).delete()
    Product.objects.filter(sku__contains=timestamp_suffix).delete()
    Warehouse.objects.filter(name__contains=timestamp_suffix).delete()
    User.objects.filter(username__contains=timestamp_suffix).delete()
    
    print("Test data cleaned up.")


if __name__ == "__main__":
    test_reservation_allocation()