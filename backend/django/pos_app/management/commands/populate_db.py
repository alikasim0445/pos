from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pos_app.models import (
    Category, Product, ProductVariant, Warehouse, 
    Inventory, Customer, Sale, SaleLine, Payment, 
    Transfer, TransferLine, AuditLog
)
from decimal import Decimal
import uuid
from django.utils import timezone
from django.db import transaction
import random


class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate the database...')
        
        # Create sample data for each model
        self.create_categories()
        self.create_warehouses()
        self.create_users()
        self.create_customers()
        self.create_products()
        self.create_product_variants()
        self.create_inventory()
        self.create_sales()
        self.create_payments()
        self.create_transfers()
        self.create_audit_logs()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample data')
        )

    def create_categories(self):
        categories = [
            "Electronics", "Clothing", "Food & Beverages", "Home & Garden", 
            "Beauty", "Sports", "Books", "Toys", "Automotive", "Health"
        ]
        
        for i, name in enumerate(categories, 1):
            Category.objects.get_or_create(
                id=i,
                defaults={
                    'name': name,
                    'description': f'Description for {name} category'
                }
            )
        self.stdout.write(f'Created {len(categories)} categories')

    def create_warehouses(self):
        warehouses = [
            ("Main Warehouse", "123 Main St, New York, NY", "John Smith", "+1-555-0101", "main@warehouse.com", 10000),
            ("North Warehouse", "456 North Ave, Chicago, IL", "Jane Doe", "+1-555-0102", "north@warehouse.com", 8000),
            ("South Warehouse", "789 South Blvd, Miami, FL", "Mike Johnson", "+1-555-0103", "south@warehouse.com", 7500),
            ("East Warehouse", "321 East Rd, Boston, MA", "Sarah Williams", "+1-555-0104", "east@warehouse.com", 9000),
            ("West Warehouse", "654 West St, Los Angeles, CA", "Robert Brown", "+1-555-0105", "west@warehouse.com", 12000),
            ("Central Warehouse", "987 Central Ave, Dallas, TX", "Emily Davis", "+1-555-0106", "central@warehouse.com", 11000),
            ("Downtown Warehouse", "147 Downtown St, Seattle, WA", "Michael Miller", "+1-555-0107", "downtown@warehouse.com", 6000),
            ("Uptown Warehouse", "258 Uptown Blvd, Denver, CO", "Jessica Wilson", "+1-555-0108", "uptown@warehouse.com", 8500),
            ("Riverside Warehouse", "369 Riverside Dr, Portland, OR", "David Taylor", "+1-555-0109", "riverside@warehouse.com", 9500),
            ("Airport Warehouse", "741 Airport Way, Atlanta, GA", "Lisa Anderson", "+1-555-0110", "airport@warehouse.com", 13000),
        ]
        
        for i, (name, location, contact_person, contact_phone, contact_email, capacity) in enumerate(warehouses, 1):
            Warehouse.objects.get_or_create(
                id=i,
                defaults={
                    'name': name,
                    'location': location,
                    'contact_person': contact_person,
                    'contact_phone': contact_phone,
                    'contact_email': contact_email,
                    'capacity': capacity
                }
            )
        self.stdout.write(f'Created {len(warehouses)} warehouses')

    def create_users(self):
        roles = ['super_admin', 'admin', 'warehouse_manager', 'store_manager', 'cashier', 'accountant', 'cashier', 'cashier', 'warehouse_manager', 'admin']
        first_names = ['Admin', 'Manager', 'Cashier', 'John', 'Jane', 'Mike', 'Sarah', 'Robert', 'Emily', 'Michael']
        last_names = ['User', 'Supervisor', 'Staff', 'Smith', 'Doe', 'Johnson', 'Williams', 'Brown', 'Davis', 'Miller']
        
        for i in range(1, 11):
            username = f'user{i:02d}'
            email = f'user{i:02d}@example.com'
            first_name = first_names[(i-1) % len(first_names)]
            last_name = last_names[(i-1) % len(last_names)]
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True
                }
            )
            
            if created:
                user.set_password('defaultpass123')
                user.save()
            
            # Update the user profile with a role
            if hasattr(user, 'userprofile'):
                user.userprofile.role = roles[(i-1) % len(roles)]
                user.userprofile.save()
            else:
                # Create UserProfile if it doesn't exist
                from pos_app.models import UserProfile
                UserProfile.objects.create(user=user, role=roles[(i-1) % len(roles)])
        
        self.stdout.write(f'Created {len(first_names)} users with roles')

    def create_customers(self):
        first_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry', 'Ivy', 'Jack']
        last_names = ['Johnson', 'Smith', 'Williams', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor', 'Anderson']
        
        for i in range(1, 11):
            Customer.objects.get_or_create(
                id=i,
                defaults={
                    'first_name': first_names[(i-1) % len(first_names)],
                    'last_name': last_names[(i-1) % len(last_names)],
                    'email': f'customer{i}@example.com',
                    'phone': f'+1-555-02{i:02d}',
                    'address': f'{i*100} Customer St, City {i}',
                    'loyalty_points': random.randint(0, 1000)
                }
            )
        self.stdout.write(f'Created {len(first_names)} customers')

    def create_products(self):
        categories = list(Category.objects.all())
        product_names = [
            "Smartphone", "Laptop", "Headphones", "Tablet", "Camera",
            "T-Shirt", "Jeans", "Dress", "Shoes", "Jacket",
            "Apple", "Banana", "Orange", "Milk", "Bread",
            "Garden Hose", "Lawn Mower", "Shovel", "Potting Soil", "Plant Seeds",
            "Lipstick", "Mascara", "Foundation", "Shampoo", "Conditioner",
            "Soccer Ball", "Basketball", "Tennis Racket", "Yoga Mat", "Dumbbell Set",
            "Fiction Novel", "Biography", "Cookbook", "Textbook", "Comic Book",
            "Action Figure", "Board Game", "Puzzle", "Doll", "Toy Car",
            "Oil Filter", "Air Filter", "Brake Pads", "Wiper Blades", "Spark Plugs",
            "Vitamin C", "Multivitamin", "Pain Reliever", "Allergy Medicine", "Probiotic"
        ]
        
        for i in range(1, 11):
            Product.objects.get_or_create(
                id=i,
                defaults={
                    'name': product_names[(i-1) % len(product_names)],
                    'sku': f'SKU-{i:04d}',
                    'barcode': f'1234567890{i:02d}',
                    'description': f'Description for product {product_names[(i-1) % len(product_names)]}',
                    'category': categories[(i-1) % len(categories)],
                    'price': Decimal(random.uniform(5.0, 500.0)).quantize(Decimal('0.01')),
                    'cost_price': Decimal(random.uniform(3.0, 300.0)).quantize(Decimal('0.01'))
                }
            )
        self.stdout.write(f'Created 10 products')

    def create_product_variants(self):
        products = list(Product.objects.all())
        variant_names = ["Small", "Medium", "Large", "XL", "Red", "Blue", "Green", "Black", "White", "256GB"]
        
        for i in range(1, 11):
            product = products[(i-1) % len(products)]
            ProductVariant.objects.get_or_create(
                id=i,
                defaults={
                    'product': product,
                    'name': variant_names[(i-1) % len(variant_names)],
                    'sku': f'VAR-{i:04d}',
                    'barcode': f'9876543210{i:02d}',
                    'additional_price': Decimal(random.uniform(0.0, 50.0)).quantize(Decimal('0.01'))
                }
            )
        self.stdout.write(f'Created 10 product variants')

    def create_inventory(self):
        products = list(Product.objects.all())
        variants = list(ProductVariant.objects.all())
        warehouses = list(Warehouse.objects.all())
        
        for i in range(1, 11):
            Inventory.objects.get_or_create(
                id=i,
                defaults={
                    'product': products[(i-1) % len(products)],
                    'variant': variants[(i-1) % len(variants)] if len(variants) > 0 else None,
                    'warehouse': warehouses[(i-1) % len(warehouses)],
                    'qty_on_hand': random.randint(10, 200),
                    'qty_reserved': random.randint(0, 20),
                    'min_stock_level': random.randint(5, 25)
                }
            )
        self.stdout.write(f'Created 10 inventory records')

    def create_sales(self):
        cashiers = list(User.objects.filter(userprofile__role__in=['cashier', 'admin', 'store_manager'])[:5])
        customers = list(Customer.objects.all())
        warehouses = list(Warehouse.objects.all())
        
        for i in range(1, 11):
            sale_date = timezone.now() - timezone.timedelta(days=random.randint(0, 30))
            
            Sale.objects.get_or_create(
                id=i,
                defaults={
                    'receipt_number': f'REC-{uuid.uuid4().hex[:8].upper()}',
                    'cashier': cashiers[(i-1) % len(cashiers)],
                    'customer': customers[(i-1) % len(customers)],
                    'warehouse': warehouses[(i-1) % len(warehouses)],
                    'total_amount': Decimal(random.uniform(10.0, 1000.0)).quantize(Decimal('0.01')),
                    'tax_amount': Decimal(random.uniform(0.5, 100.0)).quantize(Decimal('0.01')),
                    'discount_amount': Decimal(random.uniform(0.0, 50.0)).quantize(Decimal('0.01')),
                    'payment_status': random.choice(['completed', 'pending', 'refunded']),
                    'sale_date': sale_date
                }
            )
        self.stdout.write(f'Created 10 sales')

    def create_payments(self):
        sales = list(Sale.objects.all())
        payment_methods = ['cash', 'card', 'mobile', 'voucher', 'credit']
        
        for i in range(1, 11):
            Payment.objects.get_or_create(
                id=i,
                defaults={
                    'sale': sales[(i-1) % len(sales)],
                    'payment_method': payment_methods[(i-1) % len(payment_methods)],
                    'amount': Decimal(random.uniform(10.0, 500.0)).quantize(Decimal('0.01')),
                    'reference': f'REF-{uuid.uuid4().hex[:8].upper()}',
                    'paid_at': timezone.now() - timezone.timedelta(days=random.randint(0, 30))
                }
            )
        self.stdout.write(f'Created 10 payments')

    def create_transfers(self):
        warehouses = list(Warehouse.objects.all())
        users = list(User.objects.filter(userprofile__role__in=['warehouse_manager', 'admin']))
        
        for i in range(1, 11):
            Transfer.objects.get_or_create(
                id=i,
                defaults={
                    'transfer_number': f'TRF-{uuid.uuid4().hex[:8].upper()}',
                    'from_warehouse': warehouses[(i-1) % len(warehouses)],
                    'to_warehouse': warehouses[(i % len(warehouses)) % len(warehouses)],  # Different warehouse
                    'requested_by': users[(i-1) % len(users)],
                    'status': random.choice(['approved', 'requested', 'in_transit', 'received'])
                }
            )
        self.stdout.write(f'Created 10 transfers')

    def create_audit_logs(self):
        users = list(User.objects.all())
        object_types = ['Product', 'Sale', 'Customer', 'User', 'Inventory', 'Category', 'Warehouse', 'Payment', 'Transfer', 'AuditLog']
        
        for i in range(1, 11):
            AuditLog.objects.get_or_create(
                id=i,
                defaults={
                    'user': users[(i-1) % len(users)],
                    'action': random.choice(['create', 'update', 'delete', 'view', 'login']),
                    'object_type': object_types[(i-1) % len(object_types)],
                    'object_id': random.randint(1, 50),
                    'timestamp': timezone.now() - timezone.timedelta(days=random.randint(0, 30)),
                    'ip_address': f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}'
                }
            )
        self.stdout.write(f'Created 10 audit logs')