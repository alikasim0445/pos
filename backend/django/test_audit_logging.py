"""
Test file to verify the audit logging and immutable transaction functionality
"""
import os
import django
from django.conf import settings
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from pos_app.models import AuditLog, Sale, Customer, Product, Category, Warehouse, Inventory
from pos_app.audit_middleware import AuditMiddleware
from pos_app.signals import set_current_user
import tempfile


class AuditLogTest(TestCase):
    def setUp(self):
        # Create a request factory for testing
        self.factory = RequestFactory()
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create other required objects
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            sku='TEST001',
            price=10.99,
            category=self.category
        )
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            location='Test Location'
        )
        
        # Create inventory for the product
        self.inventory = Inventory.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            qty_on_hand=100
        )

    def test_audit_log_creation(self):
        """Test that audit logs are created for user actions"""
        # Set current user for audit logging
        set_current_user(self.user)
        
        # Create a sale
        sale = Sale.objects.create(
            receipt_number='TEST001',
            cashier=self.user,
            customer=self.customer,
            warehouse=self.warehouse,
            total_amount=21.98,  # 2 items at $10.99 each
            payment_status='completed',
            sale_type='sale'
        )
        
        # Check if audit log was created
        audit_logs = AuditLog.objects.filter(
            object_type='sale',
            object_id=sale.id
        )
        
        self.assertEqual(audit_logs.count(), 1)
        log = audit_logs.first()
        self.assertEqual(log.action, 'create')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.object_type, 'sale')
        self.assertEqual(log.object_id, sale.id)

    def test_sale_immutability(self):
        """Test that sales become immutable after completion"""
        # Create a completed sale
        sale = Sale.objects.create(
            receipt_number='TEST002',
            cashier=self.user,
            customer=self.customer,
            warehouse=self.warehouse,
            total_amount=10.99,
            payment_status='completed',  # Completed sale should be locked
            sale_type='sale'
        )
        
        # Reload the sale to ensure it's locked
        sale.refresh_from_db()
        
        # Verify the sale is locked after completion
        self.assertTrue(sale.is_locked)
        self.assertIsNotNone(sale.locked_at)
        self.assertEqual(sale.original_total, 10.99)
        
        # Try to modify the sale - this should raise an error due to immutability
        sale.total_amount = 15.99  # Attempt to change
        with self.assertRaises(Exception):  # This should raise a validation error
            sale.save()

    def test_return_immutability(self):
        """Test that returns become immutable after processing"""
        # Create a sale first
        original_sale = Sale.objects.create(
            receipt_number='TEST003',
            cashier=self.user,
            customer=self.customer,
            warehouse=self.warehouse,
            total_amount=10.99,
            payment_status='completed',
            sale_type='sale'
        )
        
        # Create a return
        from pos_app.models import Return
        return_obj = Return.objects.create(
            original_sale=original_sale,
            customer=self.customer,
            total_amount=10.99,
            status='processed',  # Processed return should be locked
            reason='Defective item'
        )
        
        # Reload to ensure it's locked
        return_obj.refresh_from_db()
        
        # Verify the return is locked after processing
        self.assertTrue(return_obj.is_locked)
        self.assertIsNotNone(return_obj.locked_at)
        self.assertEqual(return_obj.original_total, 10.99)
        
        # Try to modify the return - this should raise an error due to immutability
        return_obj.total_amount = 15.99  # Attempt to change
        with self.assertRaises(Exception):  # This should raise a validation error
            return_obj.save()

    def test_login_logout_logging(self):
        """Test that login and logout actions are logged"""
        # This would be tested in the actual API calls
        # For now, we'll just verify that the audit log model works
        AuditLog.objects.create(
            user=self.user,
            action='login',
            object_type='session',
            object_id=self.user.id,
            object_repr=f'User {self.user.username} logged in',
            ip_address='127.0.0.1'
        )
        
        login_logs = AuditLog.objects.filter(
            user=self.user,
            action='login'
        )
        
        self.assertGreaterEqual(login_logs.count(), 1)


def run_audit_tests():
    """Function to run the audit tests"""
    import unittest
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(AuditLogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    # Set up Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_project.settings')
    django.setup()
    
    # Run the tests
    success = run_audit_tests()
    if success:
        print("\n✓ All audit and logging tests passed!")
    else:
        print("\n✗ Some tests failed!")