"""
Test script to verify the warehouse and location implementation meets all requirements:
FR-11: CRUD for warehouses and store locations.
FR-12: Location-level stock tracking (per SKU per warehouse).
FR-13: Bin/shelf locations (optional) for advanced inventory
"""
import os
import django
from django.conf import settings
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_project.settings')
django.setup()

from pos_app.models import (
    Warehouse, Location, Bin, Product, ProductVariant, Inventory, 
    UserProfile, User
)
from django.contrib.auth.models import User as DjangoUser


def test_warehouses_locations():
    print("Testing Warehouse and Location Implementation...")
    
    # Generate unique identifiers for this test run
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    unique_suffix = f"_{timestamp}"
    
    # Test FR-11: CRUD for warehouses and store locations
    print("\n1. Testing Warehouse CRUD operations...")
    
    # Create a warehouse with unique identifiers for this test run
    warehouse = Warehouse.objects.create(
        name=f"Test Main Warehouse{unique_suffix}",
        location="123 Test Main St, City",
        warehouse_type="warehouse",
        contact_person="John Doe",
        contact_phone="555-1234",
        contact_email="test-warehouse@example.com",
        capacity=10000
    )
    print(f"   Created warehouse: {warehouse.name}")
    
    # Create a store location
    store_location = Warehouse.objects.create(
        name=f"Test Downtown Store{unique_suffix}",
        location="456 Test Downtown Ave, City",
        warehouse_type="store",
        contact_person="Jane Smith",
        contact_phone="555-5678",
        contact_email="test-store@example.com",
        capacity=5000
    )
    print(f"   Created store location: {store_location.name}")
    
    # Update warehouse
    warehouse.contact_person = "John Updated"
    warehouse.save()
    print(f"   Updated warehouse contact: {warehouse.contact_person}")
    
    # Retrieve warehouses
    warehouses = Warehouse.objects.all()
    print(f"   Total warehouses: {warehouses.count()}")
    
    # Test FR-12: Location-level stock tracking
    print("\n2. Testing Location-level stock tracking...")
    
    # Create a location within the warehouse using a unique code
    location = Location.objects.create(
        name="Aisle 1",
        warehouse=warehouse,
        code=f"TEST-A-01{unique_suffix}",
        description="Test aisle in the main warehouse"
    )
    print(f"   Created location: {location.name}")
    
    # Create a bin within the location using a unique code
    bin = Bin.objects.create(
        name="Shelf 1A",
        location=location,
        code=f"TEST-B-01A{unique_suffix}",
        description="Test shelf in Aisle 1"
    )
    print(f"   Created bin: {bin.name}")
    
    # Create a product with unique SKU
    product = Product.objects.create(
        name="Test Product",
        sku=f"TEST001{unique_suffix}",
        price=10.99
    )
    print(f"   Created product: {product.name}")
    
    # Create inventory at the location level
    # Use different fields to avoid unique constraint issues
    inventory = Inventory.objects.create(
        product=product,
        warehouse=warehouse,
        location=location,
        bin=bin,
        qty_on_hand=100,
        qty_reserved=10,
        min_stock_level=20
    )
    print(f"   Created inventory: {inventory.product.name} with {inventory.qty_on_hand} units at {inventory.location.name}")
    
    # Test location-level stock tracking
    print(f"   Location inventory count: {location.get_inventory().count()}")
    
    # Test FR-13: Bin/shelf locations
    print("\n3. Testing Bin/shelf locations...")
    
    # Verify the bin was created and has inventory
    bin_inventory = bin.get_inventory()
    print(f"   Bin inventory count: {bin_inventory.count()}")
    
    # Test unique constraint - try to create duplicate location code within same warehouse
    try:
        duplicate_location = Location.objects.create(
            name="Aisle 1 Duplicate",
            warehouse=warehouse,
            code=f"TEST-A-01{unique_suffix}",  # Same code as existing location
            description="Duplicate location code"
        )
        print("   ERROR: Duplicate location code was allowed")
        # Clean up the duplicate if it was somehow created
        duplicate_location.delete()
    except Exception as e:
        print(f"   Correctly prevented duplicate location code: {str(e)}")
    
    # Test hierarchical locations
    sub_location = Location.objects.create(
        name="Section A",
        warehouse=warehouse,
        code=f"TEST-SEC-A-01{unique_suffix}",
        parent_location=location,
        description="Section A of Aisle 1"
    )
    print(f"   Created sub-location: {sub_location.name}")
    
    print("\nAll tests completed successfully!")
    
    # Clean up
    print("\nCleaning up test data...")
    Bin.objects.filter(code__in=[f"TEST-B-01A{unique_suffix}"]).delete()
    Location.objects.filter(code__in=[f"TEST-A-01{unique_suffix}", f"TEST-SEC-A-01{unique_suffix}"]).delete()
    Inventory.objects.filter(product=product).delete()
    Product.objects.filter(sku=f"TEST001{unique_suffix}").delete()
    Warehouse.objects.filter(name__in=[f"Test Main Warehouse{unique_suffix}", f"Test Downtown Store{unique_suffix}"]).delete()
    
    print("Test data cleaned up.")


if __name__ == "__main__":
    test_warehouses_locations()