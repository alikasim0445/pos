from django.core.management.base import BaseCommand
from django.utils import timezone
from pos_app.models import Promotion, Coupon, Product, Category
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed the database with sample promotions and coupons'

    def handle(self, *args, **options):
        self.stdout.write('Starting to seed promotions and coupons...')
        
        # First, get or create categories separately to avoid PK conflicts
        categories = []
        for name in ['Electronics', 'Clothing', 'Books', 'Food', 'Home & Garden']:
            try:
                cat = Category.objects.get(name=name)
                self.stdout.write(f'Category {name} already exists')
            except Category.DoesNotExist:
                cat = Category.objects.create(
                    name=name,
                    description=f'{name} category'
                )
                self.stdout.write(f'Created category: {name}')
            categories.append(cat)
        
        # Create some sample products if they don't exist
        sample_products = [
            {'name': 'Smartphone', 'sku': 'ELEC001', 'price': Decimal('499.99')},
            {'name': 'Laptop', 'sku': 'ELEC002', 'price': Decimal('899.99')},
            {'name': 'T-Shirt', 'sku': 'CLOT001', 'price': Decimal('19.99')},
            {'name': 'Jeans', 'sku': 'CLOT002', 'price': Decimal('49.99')},
            {'name': 'Cookware Set', 'sku': 'HOME001', 'price': Decimal('129.99')},
        ]
        
        products = []
        for prod_data in sample_products:
            # Get a random category for the product
            cat_index = len(products) % len(categories)
            prod, created = Product.objects.get_or_create(
                sku=prod_data['sku'],
                defaults={
                    'name': prod_data['name'],
                    'category': categories[cat_index],
                    'price': prod_data['price']
                }
            )
            products.append(prod)
            if created:
                self.stdout.write(f'Created product: {prod.name}')
        
        # Create sample promotions
        promotions = [
            {
                'name': 'Summer Electronics Sale',
                'promotion_type': 'percentage',
                'description': '20% off on all electronics',
                'discount_value': Decimal('20.00'),
                'start_date': timezone.now(),
                'end_date': timezone.now().replace(month=12, day=31),
                'is_active': True,
            },
            {
                'name': 'Back to School Discount',
                'promotion_type': 'fixed_amount',
                'description': '$10 off on school supplies',
                'discount_value': Decimal('10.00'),
                'start_date': timezone.now(),
                'end_date': timezone.now().replace(month=9, day=30),
                'is_active': True,
            },
            {
                'name': 'Buy One Get One Free',
                'promotion_type': 'buy_x_get_y',
                'description': 'Buy one get second item free',
                'discount_value': Decimal('1.00'),  # For BOGO, this represents the "get" quantity
                'start_date': timezone.now(),
                'end_date': timezone.now().replace(month=11, day=30),
                'is_active': True,
            },
            {
                'name': 'New Year Special',
                'promotion_type': 'percentage',
                'description': '25% off sitewide',
                'discount_value': Decimal('25.00'),
                'start_date': timezone.now(),
                'end_date': timezone.now().replace(month=1, day=31),
                'is_active': True,
            }
        ]
        
        for promo_data in promotions:
            promo, created = Promotion.objects.get_or_create(
                name=promo_data['name'],
                defaults=promo_data
            )
            if created:
                self.stdout.write(f'Created promotion: {promo.name}')
            else:
                self.stdout.write(f'Promotion {promo.name} already exists')
        
        # Add some products to promotions
        all_promotions = Promotion.objects.all()
        for i, promo in enumerate(all_promotions):
            if products:
                # Add a few products to each promotion based on their index
                for j in range(min(2, len(products))):
                    if j < len(products):
                        prod_index = (i + j) % len(products)
                        promo.products.add(products[prod_index])
        
        # Create sample coupons
        coupons = [
            {
                'code': 'WELCOME10',
                'discount_type': 'percentage',
                'discount_value': Decimal('10.00'),
                'description': 'Welcome discount for new customers',
                'minimum_order_amount': Decimal('50.00'),
                'usage_limit': 100,
                'used_count': 0,
                'is_active': True,
                'valid_from': timezone.now(),
                'valid_until': timezone.now().replace(month=12, day=31),
            },
            {
                'code': 'SAVE20NOW',
                'discount_type': 'fixed_amount',
                'discount_value': Decimal('20.00'),
                'description': 'Limited time offer',
                'minimum_order_amount': Decimal('100.00'),
                'usage_limit': 50,
                'used_count': 0,
                'is_active': True,
                'valid_from': timezone.now(),
                'valid_until': timezone.now().replace(month=10, day=31),
            },
            {
                'code': 'FREESHIP30',
                'discount_type': 'free_shipping',
                'discount_value': Decimal('0.00'),
                'description': 'Free shipping on orders over $30',
                'minimum_order_amount': Decimal('30.00'),
                'usage_limit': 200,
                'used_count': 0,
                'is_active': True,
                'valid_from': timezone.now(),
                'valid_until': timezone.now().replace(month=11, day=30),
            }
        ]
        
        for coupon_data in coupons:
            coupon, created = Coupon.objects.get_or_create(
                code=coupon_data['code'],
                defaults=coupon_data
            )
            if created:
                self.stdout.write(f'Created coupon: {coupon.code}')
            else:
                self.stdout.write(f'Coupon {coupon.code} already exists')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded promotions and coupons!')
        )