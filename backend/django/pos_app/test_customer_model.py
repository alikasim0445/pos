import os
import django
from django.test import TestCase
from pos_app.models import Customer
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_project.settings')
django.setup()

class CustomerModelTest(TestCase):
    """
    Test case for validating the Customer model, specifically the store_credit and notes fields.
    """

    def test_customer_store_credit_and_notes(self):
        """
        Tests that the `store_credit` and `notes` fields of the Customer model can be set and retrieved correctly.
        """
        # Create a customer with store credit and notes
        customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            store_credit=Decimal('100.50'),
            notes="This is a test note for the customer."
        )

        # Retrieve the customer from the database
        saved_customer = Customer.objects.get(id=customer.id)

        # Assert that the store_credit and notes are saved correctly
        self.assertEqual(saved_customer.store_credit, Decimal('100.50'))
        self.assertEqual(saved_customer.notes, "This is a test note for the customer.")

        print("\n✓ Customer model test passed: store_credit and notes fields are working as expected.")

if __name__ == '__main__':
    # This allows running the test script directly
    import unittest
    unittest.main()

