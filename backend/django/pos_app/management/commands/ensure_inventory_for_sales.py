from django.core.management.base import BaseCommand
from pos_app.models import Product, Warehouse, Inventory, ProductVariant
from django.db import transaction


class Command(BaseCommand):
    help = 'Ensure inventory records exist for all products in all warehouses where sales might occur'

    def add_arguments(self, parser):
        parser.add_argument(
            '--qty',
            type=int,
            default=100,
            help='Quantity to set for newly created inventory records (default: 100)'
        )

    def handle(self, *args, **options):
        qty = options['qty']
        products = Product.objects.all()
        warehouses = Warehouse.objects.all()

        created_count = 0
        
        for product in products:
            for warehouse in warehouses:
                # Check for all variants of the product
                variants = ProductVariant.objects.filter(product=product)
                
                # Create inventory for base product (no variant)
                # Use get_or_create with additional constraints to avoid conflicts
                inventory, created = Inventory.objects.get_or_create(
                    product=product,
                    warehouse=warehouse,
                    variant=None,
                    location=None,
                    bin=None,
                    defaults={
                        'qty_on_hand': qty,
                        'qty_reserved': 0,
                        'min_stock_level': 10
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        f'Created inventory: Product {product.id} in Warehouse {warehouse.id} (no variant)'
                    )
                
                # Create inventory for each variant of the product
                for variant in variants:
                    variant_inventory, variant_created = Inventory.objects.get_or_create(
                        product=product,
                        warehouse=warehouse,
                        variant=variant,
                        location=None,
                        bin=None,
                        defaults={
                            'qty_on_hand': qty,
                            'qty_reserved': 0,
                            'min_stock_level': 10
                        }
                    )
                    if variant_created:
                        created_count += 1
                        self.stdout.write(
                            f'Created inventory: Product {product.id} Variant {variant.id} in Warehouse {warehouse.id}'
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully ensured inventory records. Created {created_count} new inventory records.'
            )
        )