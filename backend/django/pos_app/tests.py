from django.test import TestCase
from pos_app.models import Product, Warehouse

class ProductModelTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Test Product", price=10.99)

    def test_product_creation(self):
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.price, 10.99)

class WarehouseModelTest(TestCase):
    def setUp(self):
        self.warehouse = Warehouse.objects.create(name="Secondary Warehouse", location="456 Secondary St")

    def test_warehouse_creation(self):
        self.assertEqual(self.warehouse.name, "Secondary Warehouse")
        self.assertEqual(self.warehouse.location, "456 Secondary St")