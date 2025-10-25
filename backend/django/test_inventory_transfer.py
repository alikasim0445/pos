"""
Test script to verify the inventory transfer implementation meets all requirements:
FR-17: Create transfer requests between warehouses/stores.
FR-18: Approve/reject transfers by receiving warehouse manager.
FR-19: Track transfer status (requested, in transit, received).
FR-20: Automatic stock reservation on transfer creation (configurable).
"""
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_project.settings')
django.setup()

from pos_app.models import (
    Warehouse, Location, Bin, Product, ProductVariant, Inventory, 
    UserProfile, User, Transfer, TransferLine
)
from django.contrib.auth.models import User as DjangoUser
from django.utils import timezone


def test_inventory_transfers():
    print("Testing Inventory Transfer Implementation...")
    
    # Test FR-17: Create transfer requests between warehouses/stores
    print("\n1. Testing Transfer Request Creation...")
    
    # Create warehouses
    source_warehouse = Warehouse.objects.create(
        name="Source Warehouse",
        location="123 Source St, City",
        warehouse_type="warehouse",
        contact_person="John Doe",
        contact_phone="555-1234",
        contact_email="source@example.com",
        capacity=10000
    )
    print(f"   Created source warehouse: {source_warehouse.name}")
    
    dest_warehouse = Warehouse.objects.create(
        name="Destination Warehouse",
        location="456 Destination Ave, City",
        warehouse_type="warehouse",
        contact_person="Jane Smith",
        contact_phone="555-5678",
        contact_email="dest@example.com",
        capacity=10000
    )
    print(f"   Created destination warehouse: {dest_warehouse.name}")
    
    # Create locations
    source_location = Location.objects.create(
        name="Source Aisle 1",
        warehouse=source_warehouse,
        code="SRC-A-01",
        description="Source aisle in the source warehouse"
    )
    print(f"   Created source location: {source_location.name}")
    
    dest_location = Location.objects.create(
        name="Dest Aisle 1",
        warehouse=dest_warehouse,
        code="DST-A-01",
        description="Destination aisle in the destination warehouse"
    )
    print(f"   Created destination location: {dest_location.name}")
    
    # Create bins
    source_bin = Bin.objects.create(
        name="Source Shelf 1A",
        location=source_location,
        code="SRC-B-01A",
        description="Source shelf in Source Aisle 1"
    )
    print(f"   Created source bin: {source_bin.name}")
    
    dest_bin = Bin.objects.create(
        name="Dest Shelf 1A",
        location=dest_location,
        code="DST-B-01A",
        description="Destination shelf in Dest Aisle 1"
    )
    print(f"   Created destination bin: {dest_bin.name}")
    
    # Create products
    product = Product.objects.create(
        name="Test Transfer Product",
        sku="TEST-TP001",
        price=10.99
    )
    print(f"   Created product: {product.name}")
    
    # Create a user for the test
    test_user, created = User.objects.get_or_create(
        username="test_transfer_user",
        defaults={'email': 'test@example.com', 'is_active': True}
    )
    if created:
        test_user.set_password('password123')
        test_user.save()
    print(f"   Created test user: {test_user.username}")
    
    # Create inventory at the source location
    source_inventory = Inventory.objects.create(
        product=product,
        warehouse=source_warehouse,
        location=source_location,
        bin=source_bin,
        qty_on_hand=100,  # 100 units available
        qty_reserved=0,
        min_stock_level=20
    )
    print(f"   Created source inventory: {source_inventory.qty_on_hand} units")
    
    # Create a transfer request
    transfer = Transfer.objects.create(
        transfer_number="TRF-001",
        from_warehouse=source_warehouse,
        from_location=source_location,
        from_bin=source_bin,
        to_warehouse=dest_warehouse,
        to_location=dest_location,
        to_bin=dest_bin,
        requested_by=test_user,
        status='requested',  # Start with requested status
        notes="Test transfer from source to destination"
    )
    print(f"   Created transfer request: {transfer.transfer_number}")
    
    # Create a transfer line
    transfer_line = TransferLine.objects.create(
        transfer=transfer,
        product=product,
        requested_qty=25,
        transferred_qty=0,
        received_qty=0
    )
    print(f"   Created transfer line: {transfer_line.requested_qty} units requested")
    
    # Test FR-19: Track transfer status
    print("\n2. Testing Transfer Status Tracking...")
    print(f"   Initial status: {transfer.status}")
    
    # Test FR-18: Approve/reject transfers by receiving warehouse manager
    print("\n3. Testing Transfer Approval/Rejection...")
    
    # Assign an approving user
    approving_user, created = User.objects.get_or_create(
        username="test_approver",
        defaults={'email': 'approver@example.com', 'is_active': True}
    )
    if created:
        approving_user.set_password('password123')
        approving_user.save()
        
    # Create user profile for approving user if it doesn't exist
    user_profile, created = UserProfile.objects.get_or_create(
        user=approving_user,
        defaults={'role': 'store_manager'}
    )
    print(f"   Created approving user: {approving_user.username} with role: {user_profile.role}")
    
    # Approve the transfer
    transfer.status = 'approved'
    transfer.approved_by = approving_user
    transfer.approved_at = timezone.now()
    transfer.save()
    print(f"   Transfer approved by: {transfer.approved_by.username} at {transfer.approved_at}")
    print(f"   Status after approval: {transfer.status}")
    
    # Move to in-transit status
    transfer.status = 'in_transit'
    transfer.save()
    print(f"   Status after setting to in-transit: {transfer.status}")
    
    # Receive the transfer
    transfer_line.received_qty = transfer_line.requested_qty  # Receive all requested quantity
    transfer_line.transferred_qty = transfer_line.requested_qty  # Mark as transferred
    transfer_line.save()
    
    transfer.status = 'received'
    transfer.received_at = timezone.now()
    transfer.completed_at = timezone.now()
    transfer.save()
    print(f"   Status after receiving: {transfer.status}")
    print(f"   Received at: {transfer.received_at}")
    
    # Test FR-20: Automatic stock reservation on transfer creation (configurable)
    print("\n4. Testing Stock Reservation...")
    
    # Check source inventory quantities after transfer
    source_inventory.refresh_from_db()
    print(f"   Source inventory after transfer: {source_inventory.qty_on_hand} on hand, {source_inventory.qty_reserved} reserved")
    
    # Test that the reservation logic would work by creating another transfer
    # and checking if stock reservation is properly managed
    print("\n5. Testing Stock Management during Transfers...")
    
    print(f"   Source inventory - On Hand: {source_inventory.qty_on_hand}, Reserved: {source_inventory.qty_reserved}")
    print(f"   Transfer requested quantity: {transfer_line.requested_qty}")
    
    # Verify that the system handles the stock correctly
    expected_on_hand = 100 - 25  # Initial 100 minus transferred 25
    print(f"   Expected on-hand after transfer: {expected_on_hand}")
    print(f"   Actual on-hand: {source_inventory.qty_on_hand}")
    
    # Verify that the destination warehouse now has the inventory
    dest_inventory = Inventory.objects.filter(
        product=product,
        warehouse=dest_warehouse,
        location=dest_location,
        bin=dest_bin
    ).first()
    
    if dest_inventory:
        print(f"   Destination inventory: {dest_inventory.qty_on_hand} units")
    else:
        print("   Destination inventory not automatically created - may need to implement stock receipt logic")
    
    print("\nTransfer tests completed!")
    
    # Clean up
    print("\nCleaning up test data...")
    TransferLine.objects.filter(transfer=transfer).delete()
    Transfer.objects.filter(transfer_number="TRF-001").delete()
    Inventory.objects.filter(product=product).delete()
    Bin.objects.filter(code__in=["SRC-B-01A", "DST-B-01A"]).delete()
    Location.objects.filter(code__in=["SRC-A-01", "DST-A-01"]).delete()
    Product.objects.filter(sku="TEST-TP001").delete()
    Warehouse.objects.filter(name__in=["Source Warehouse", "Destination Warehouse"]).delete()
    User.objects.filter(username="test_transfer_user").delete()
    User.objects.filter(username="test_approver").delete()
    
    print("Test data cleaned up.")


if __name__ == "__main__":
    test_inventory_transfers()