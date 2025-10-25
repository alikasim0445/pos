"""
Test case to reproduce the inventory validation error
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from pos_app.models import Warehouse, Location, Inventory, Product, Category


class InventoryValidationTest(TestCase):
    def setUp(self):
        # Create a category
        self.category = Category.objects.create(name="Test Category")
        
        # Create a product
        self.product = Product.objects.create(
            name="Test Product",
            sku="TEST001",
            price=10.00,
            category=self.category
        )
        
        # Create first warehouse
        self.warehouse1 = Warehouse.objects.create(
            name="Warehouse 1",
            location="Location 1"
        )
        
        # Create second warehouse
        self.warehouse2 = Warehouse.objects.create(
            name="Warehouse 2", 
            location="Location 2"
        )
        
        # Create a location that belongs to warehouse 1
        self.location1 = Location.objects.create(
            name="Location 1",
            code="L001",
            warehouse=self.warehouse1
        )

    def test_inventory_validation_error(self):
        """
        Test that creating inventory with location that doesn't belong to warehouse
        raises the expected validation error
        """
        # Try to create inventory with warehouse2 but location from warehouse1
        # This should trigger the validation error
        inventory = Inventory(
            product=self.product,
            warehouse=self.warehouse2,  # Different warehouse
            location=self.location1,    # Location from different warehouse
            qty_on_hand=10
        )
        
        # This should raise a ValidationError
        with self.assertRaises(ValidationError) as context:
            inventory.full_clean()  # This calls the model's clean method
        
        # Print the error to see the exact message
        print("Validation Error:", str(context.exception))
        print("Error dict:", context.exception.message_dict)
        
        # The error should contain the message about location belonging to warehouse
        self.assertIn('Selected location must belong to the selected warehouse.', str(context.exception))