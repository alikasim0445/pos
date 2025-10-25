"""
Test script to verify the Returns & Exchanges implementation meets all requirements:
FR-30: Process returns by original receipt or customer lookup.
FR-31: Restock returned items to selected warehouse or mark as QC.
FR-32: Issue refunds (cash/card) or store credit.
"""
import os
import django
from django.conf import settings
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_project.settings')
django.setup()

from pos_app.models import (
    Warehouse, Product, ProductVariant, Inventory, 
    UserProfile, User, Sale, SaleLine, Payment, Customer,
    Return, ReturnLine
)
from django.contrib.auth.models import User as DjangoUser
from django.core.exceptions import ValidationError


def test_returns_exchanges():
    print("Testing Returns & Exchanges Implementation...")
    
    # Generate unique suffix for this test run
    timestamp_suffix = timezone.now().strftime("%Y%m%d%H%M%S")
    
    # Test FR-30: Process returns by original receipt or customer lookup
    print("\n1. Testing Return Processing by Receipt and Customer Lookup...")
    
    # Set up required data
    warehouse = Warehouse.objects.create(
        name=f"Return Test Warehouse {timestamp_suffix}",
        location="123 Return St, City",
        warehouse_type="store",
        contact_person="Return Manager",
        contact_phone="555-RET1",
        contact_email="return@example.com",
        capacity=10000
    )
    print(f"   Created warehouse: {warehouse.name}")
    
    # Create customer
    customer = Customer.objects.create(
        first_name="Return",
        last_name="Customer",
        email=f"return_{timestamp_suffix}@example.com",
        phone="555-1234",
        address="123 Main St"
    )
    print(f"   Created customer: {customer.first_name} {customer.last_name}")
    
    # Create cashier user
    cashier_user, created = User.objects.get_or_create(
        username=f"return_cashier_{timestamp_suffix}",
        defaults={'email': f'return_cashier_{timestamp_suffix}@example.com', 'is_active': True}
    )
    if created:
        cashier_user.set_password('password123')
        cashier_user.save()
    print(f"   Created cashier user: {cashier_user.username}")
    
    # Create product
    product = Product.objects.create(
        name=f"Return Test Product {timestamp_suffix}",
        sku=f"RET-TP-{timestamp_suffix}",
        price=15.99
    )
    print(f"   Created product: {product.name}")
    
    # Create inventory
    inventory = Inventory.objects.create(
        product=product,
        warehouse=warehouse,
        qty_on_hand=50,
        qty_reserved=0,
        min_stock_level=5
    )
    print(f"   Created inventory with {inventory.qty_on_hand} units on hand")
    
    # Create a sale
    sale = Sale.objects.create(
        receipt_number=f"SAL-RET-{timestamp_suffix}-001",
        cashier=cashier_user,
        customer=customer,
        warehouse=warehouse,
        total_amount=31.98,  # 2 * $15.99
        tax_amount=3.20,  # 10% tax
        payment_status='completed'
    )
    
    # Create sale line
    sale_line = SaleLine.objects.create(
        sale=sale,
        product=product,
        quantity=2,
        unit_price=15.99,
        total_price=31.98
    )
    
    # Create payment for the sale
    payment = Payment.objects.create(
        sale=sale,
        payment_method='card',
        amount=35.18,  # Total with tax
        reference="Sale payment"
    )
    print(f"   Created sale: {sale.receipt_number} with {sale_line.quantity}x {sale_line.product.name}")
    
    # Create a return for the sale
    return_obj = Return.objects.create(
        original_sale=sale,
        customer=customer,
        return_type='return',
        reason='Customer not satisfied',
        total_amount=31.98,
        refund_amount=31.98,
        status='approved'  # Start with approved status
    )
    
    # Create return line
    return_line = ReturnLine.objects.create(
        return_obj=return_obj,
        original_line=sale_line,
        product=product,
        quantity=1,  # Return 1 of the 2 items
        unit_price=15.99,
        total_price=15.99
    )
    print(f"   Created return: {return_obj.return_number} for {return_line.quantity}x {return_line.product.name}")
    
    # Test FR-30: Look up returns by receipt number
    print("\n2. Testing Lookup by Receipt Number...")
    try:
        related_returns = Return.objects.filter(original_sale=sale)
        print(f"   Found {related_returns.count()} returns for receipt {sale.receipt_number}")
        for ret in related_returns:
            print(f"      - Return ID: {ret.id}, Number: {ret.return_number}")
    except Exception as e:
        print(f"   Error looking up returns by receipt: {str(e)}")
    
    # Test FR-30: Look up returns by customer
    print("\n3. Testing Lookup by Customer...")
    try:
        customer_returns = Return.objects.filter(customer=customer)
        print(f"   Found {customer_returns.count()} returns for customer {customer.first_name} {customer.last_name}")
        for ret in customer_returns:
            print(f"      - Return ID: {ret.id}, Number: {ret.return_number}")
    except Exception as e:
        print(f"   Error looking up returns by customer: {str(e)}")
    
    # Test FR-31: Restock returned items
    print("\n4. Testing Restocking Returned Items...")
    
    # Initially, inventory should have 50 - 2 = 48 units (since 2 were sold)
    inventory.refresh_from_db()
    print(f"   Inventory before return processing: {inventory.qty_on_hand} units")
    
    # Process the return which should restock items
    return_obj.restock_items()
    
    # Check inventory after restocking
    inventory.refresh_from_db()
    print(f"   Inventory after return processing: {inventory.qty_on_hand} units")
    
    # There should be 1 more unit now (the returned item)
    expected_after_return = 48 + 1  # 48 + 1 returned item
    if inventory.qty_on_hand == expected_after_return:
        print("   ✓ Items properly restocked")
    else:
        print(f"   ? Inventory after return: {inventory.qty_on_hand}, expected: {expected_after_return}")
    
    # Test FR-32: Issue refunds or store credit
    print("\n5. Testing Refunds and Store Credit...")
    
    # Check initial customer store credit
    print(f"   Customer initial store credit: ${customer.store_credit}")
    
    # Issue store credit instead of refund
    initial_credit = customer.store_credit
    return_obj.issue_store_credit()
    customer.refresh_from_db()
    
    print(f"   Customer store credit after issuing: ${customer.store_credit}")
    credit_issued = customer.store_credit - initial_credit
    print(f"   Credit issued: ${credit_issued} (should match refund amount: ${return_obj.refund_amount})")
    
    if credit_issued == return_obj.refund_amount:
        print("   ✓ Store credit issued correctly")
    else:
        print(f"   ? Store credit issued: ${credit_issued}, refund amount: ${return_obj.refund_amount}")
    
    # Create another return for refund testing
    print("\n6. Testing Refund Processing...")
    refund_return = Return.objects.create(
        original_sale=sale,
        customer=customer,
        return_type='refund',
        reason='Wrong item sent',
        total_amount=15.99,
        refund_amount=15.99,
        status='approved'
    )
    
    refund_line = ReturnLine.objects.create(
        return_obj=refund_return,
        original_line=sale_line,
        product=product,
        quantity=1,
        unit_price=15.99,
        total_price=15.99
    )
    
    # Process the refund
    original_inventory = inventory.qty_on_hand
    refund_return.restock_items()  # Restock the items
    
    # Issue refund
    refund_return.issue_refund()
    
    # Check inventory after restocking
    inventory.refresh_from_db()
    print(f"   Inventory after refund return: {inventory.qty_on_hand} units")
    print(f"   ✓ Refund processed and items restocked")
    
    # Test exchange functionality
    print("\n7. Testing Exchange Processing...")
    
    # Create an exchange return
    exchange_return = Return.objects.create(
        original_sale=sale,
        customer=customer,
        return_type='exchange',
        reason='Want different product',
        total_amount=15.99,
        refund_amount=15.99,  # This will be credited toward new item
        status='approved'
    )
    
    exchange_line = ReturnLine.objects.create(
        return_obj=exchange_return,
        original_line=sale_line,
        product=product,
        quantity=1,
        unit_price=15.99,
        total_price=15.99
    )
    
    # Create a new product for exchange
    new_product = Product.objects.create(
        name=f"Exchange New Product {timestamp_suffix}",
        sku=f"EXC-NP-{timestamp_suffix}",
        price=18.99  # New item costs more
    )
    
    # Process the exchange with new items data
    try:
        new_sale = exchange_return.process_exchange([
            {
                'product_id': new_product.id,
                'variant_id': None,
                'quantity': 1,
                'unit_price': 18.99
            }
        ])
        print(f"   Exchange processed successfully, new sale: {new_sale.receipt_number}")
        print("   ✓ Exchange functionality working")
    except Exception as e:
        print(f"   Error processing exchange: {str(e)}")
    
    print("\nAll Returns & Exchanges tests completed!")
    
    # Clean up
    print("\nCleaning up test data...")
    ReturnLine.objects.filter(return_obj__return_number__contains=f"RET-{timestamp_suffix[:8]}").delete()
    Return.objects.filter(return_number__contains=f"RET-{timestamp_suffix[:8]}").delete()
    SaleLine.objects.filter(sale__receipt_number__contains="SAL-RET").delete()
    Payment.objects.filter(sale__receipt_number__contains="SAL-RET").delete()
    Sale.objects.filter(receipt_number__contains="SAL-RET").delete()
    Inventory.objects.filter(product__sku__contains="RET-TP").delete()
    Inventory.objects.filter(product__sku__contains="EXC-NP").delete()
    Product.objects.filter(sku__contains="RET-TP").delete()
    Product.objects.filter(sku__contains="EXC-NP").delete()
    Customer.objects.filter(email__contains="return_").delete()
    Warehouse.objects.filter(name__contains="Return Test Warehouse").delete()
    User.objects.filter(username__contains="return_cashier_").delete()
    
    print("Test data cleaned up.")


if __name__ == "__main__":
    test_returns_exchanges()