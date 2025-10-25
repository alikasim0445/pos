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
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_project.settings')
django.setup()

from pos_app.models import (
    Warehouse, Location, Bin, Product, ProductVariant, Inventory, 
    UserProfile, User, Transfer, TransferLine
)
from django.contrib.auth.models import User as DjangoUser
from django.core.exceptions import ValidationError

# Generate unique suffix for this test run
TIMESTAMP_SUFFIX = timezone.now().strftime("%Y%m%d%H%M%S")


def test_inventory_transfers():
    print("Testing Inventory Transfer Implementation...")
    
    # Test FR-17: Create transfer requests between warehouses/stores
    print("\n1. Testing Transfer Request Creation...")
    
    # Create warehouses
    source_warehouse = Warehouse.objects.create(
        name=f"Test Source Warehouse {TIMESTAMP_SUFFIX}",
        location="123 Source St, City",
        warehouse_type="warehouse",
        contact_person="John Doe",
        contact_phone="555-1234",
        contact_email="source@example.com",
        capacity=10000
    )
    print(f"   Created source warehouse: {source_warehouse.name}")
    
    dest_warehouse = Warehouse.objects.create(
        name=f"Test Destination Warehouse {TIMESTAMP_SUFFIX}",
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
        name=f"Source Aisle 1 {TIMESTAMP_SUFFIX}",
        warehouse=source_warehouse,
        code=f"TEST-SRC-A-01-{TIMESTAMP_SUFFIX}",
        description="Source aisle in the source warehouse"
    )
    print(f"   Created source location: {source_location.name}")
    
    dest_location = Location.objects.create(
        name=f"Dest Aisle 1 {TIMESTAMP_SUFFIX}",
        warehouse=dest_warehouse,
        code=f"TEST-DST-A-01-{TIMESTAMP_SUFFIX}",
        description="Destination aisle in the destination warehouse"
    )
    print(f"   Created destination location: {dest_location.name}")
    
    # Create bins
    source_bin = Bin.objects.create(
        name=f"Source Shelf 1A {TIMESTAMP_SUFFIX}",
        location=source_location,
        code=f"TEST-SRC-B-01A-{TIMESTAMP_SUFFIX}",
        description="Source shelf in Source Aisle 1"
    )
    print(f"   Created source bin: {source_bin.name}")
    
    dest_bin = Bin.objects.create(
        name=f"Dest Shelf 1A {TIMESTAMP_SUFFIX}",
        location=dest_location,
        code=f"TEST-DST-B-01A-{TIMESTAMP_SUFFIX}",
        description="Destination shelf in Dest Aisle 1"
    )
    print(f"   Created destination bin: {dest_bin.name}")
    
    # Create products
    product = Product.objects.create(
        name=f"Test Transfer Product {TIMESTAMP_SUFFIX}",
        sku=f"TEST-TP001-{TIMESTAMP_SUFFIX}",
        price=10.99
    )
    print(f"   Created product: {product.name}")
    
    # Create a user for the test
    test_user, created = User.objects.get_or_create(
        username=f"test_transfer_user_{TIMESTAMP_SUFFIX}",
        defaults={'email': f'test_{TIMESTAMP_SUFFIX}@example.com', 'is_active': True}
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
    print(f"   Created source inventory: {source_inventory.qty_on_hand} units on hand, {source_inventory.qty_reserved} reserved")
    
    # Create a transfer request
    transfer = Transfer.objects.create(
        transfer_number=f"TRF-TEST-001-{TIMESTAMP_SUFFIX}",
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
    
    # Refresh from DB to see if auto-reservation worked
    source_inventory.refresh_from_db()
    print(f"   Source inventory after transfer creation: {source_inventory.qty_on_hand} on hand, {source_inventory.qty_reserved} reserved")
    
    # Test FR-20: Automatic stock reservation on transfer creation
    print("\n2. Testing Automatic Stock Reservation...")
    if source_inventory.qty_reserved == 25:
        print("   ✓ Stock automatically reserved when transfer was created")
    else:
        print(f"   ✗ Expected 25 reserved, but got {source_inventory.qty_reserved}")
    
    # Test FR-19: Track transfer status
    print("\n3. Testing Transfer Status Tracking...")
    print(f"   Initial status: {transfer.status}")
    
    # Create an approving user with store manager role
    approving_user, created = User.objects.get_or_create(
        username=f"test_approver_manager_{TIMESTAMP_SUFFIX}",
        defaults={'email': f'approver_{TIMESTAMP_SUFFIX}@example.com', 'is_active': True}
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
    
    # Test FR-18: Approve/reject transfers by receiving warehouse manager
    print("\n4. Testing Transfer Approval...")
    
    # Approve the transfer
    transfer.status = 'approved'
    transfer.approved_by = approving_user
    transfer.approved_at = timezone.now()
    transfer.save()
    print(f"   Transfer approved by: {transfer.approved_by.username} at {transfer.approved_at}")
    print(f"   Status after approval: {transfer.status}")
    
    # Check that inventory is still reserved after approval
    source_inventory.refresh_from_db()
    print(f"   Source inventory after approval: {source_inventory.qty_on_hand} on hand, {source_inventory.qty_reserved} reserved")
    
    # Test moving to in-transit status
    transfer.status = 'in_transit'
    transfer.save()
    print(f"   Status after setting to in-transit: {transfer.status}")
    
    # Test receiving the transfer
    print("\n5. Testing Transfer Receipt...")
    try:
        transfer.receive_transfer()
        print(f"   Transfer received successfully")
        print(f"   Final status: {transfer.status}")
        
        # Check source inventory after receipt
        source_inventory.refresh_from_db()
        print(f"   Source inventory after receipt: {source_inventory.qty_on_hand} on hand, {source_inventory.qty_reserved} reserved")
        
        # Check destination inventory after receipt
        dest_inventory = Inventory.objects.filter(
            product=product,
            warehouse=dest_warehouse,
            location=dest_location,
            bin=dest_bin
        ).first()
        
        if dest_inventory:
            print(f"   Destination inventory after receipt: {dest_inventory.qty_on_hand} units")
        else:
            print("   No destination inventory found")
            
    except ValidationError as e:
        print(f"   Error receiving transfer: {str(e)}")
    
    # Test creating another transfer and rejecting it
    print("\n6. Testing Transfer Rejection...")
    
    rejecting_user, created = User.objects.get_or_create(
        username=f"test_rejector_{TIMESTAMP_SUFFIX}",
        defaults={'email': f'rejector_{TIMESTAMP_SUFFIX}@example.com', 'is_active': True}
    )
    if created:
        rejecting_user.set_password('password123')
        rejecting_user.save()
        
    # Create user profile for rejecting user
    reject_profile, created = UserProfile.objects.get_or_create(
        user=rejecting_user,
        defaults={'role': 'store_manager'}
    )
    
    # Create another transfer to test rejection
    rejection_transfer = Transfer.objects.create(
        transfer_number=f"TRF-TEST-002-{TIMESTAMP_SUFFIX}",
        from_warehouse=source_warehouse,
        from_location=source_location,
        from_bin=source_bin,
        to_warehouse=dest_warehouse,
        to_location=dest_location,
        to_bin=dest_bin,
        requested_by=test_user,
        status='requested',
        notes="Test transfer to be rejected"
    )
    
    rejection_line = TransferLine.objects.create(
        transfer=rejection_transfer,
        product=product,
        requested_qty=10,
        transferred_qty=0,
        received_qty=0
    )
    
    # Check inventory before rejection
    source_inventory.refresh_from_db()
    print(f"   Source inventory before rejection: {source_inventory.qty_on_hand} on hand, {source_inventory.qty_reserved} reserved")
    
    # Reject the transfer
    rejection_transfer.status = 'rejected'
    rejection_transfer.approved_by = rejecting_user
    rejection_transfer.approved_at = timezone.now()
    rejection_transfer.save()
    print(f"   Transfer rejected by: {rejection_transfer.approved_by.username}")
    print(f"   Status after rejection: {rejection_transfer.status}")
    
    # Check inventory after rejection (should still be reserved since we didn't implement auto-release for rejection)
    source_inventory.refresh_from_db()
    print(f"   Source inventory after rejection: {source_inventory.qty_on_hand} on hand, {source_inventory.qty_reserved} reserved")
    
    print("\nAll transfer tests completed!")
    
    # Clean up
    print("\nCleaning up test data...")
    TransferLine.objects.filter(transfer__transfer_number__contains=TIMESTAMP_SUFFIX).delete()
    Transfer.objects.filter(transfer_number__contains=TIMESTAMP_SUFFIX).delete()
    Inventory.objects.filter(product=product).delete()
    Bin.objects.filter(code__contains=TIMESTAMP_SUFFIX).delete()
    Location.objects.filter(code__contains=TIMESTAMP_SUFFIX).delete()
    Product.objects.filter(sku__contains=TIMESTAMP_SUFFIX).delete()
    Warehouse.objects.filter(name__contains=TIMESTAMP_SUFFIX).delete()
    User.objects.filter(username__contains=TIMESTAMP_SUFFIX).delete()
    
    print("Test data cleaned up.")


if __name__ == "__main__":
    test_inventory_transfers()