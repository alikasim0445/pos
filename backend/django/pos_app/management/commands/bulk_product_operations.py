import csv
import json
from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from pos_app.models import Product, Category
import requests
from io import StringIO
from datetime import datetime

class Command(BaseCommand):
    help = 'Bulk import/export products via CSV/Excel'

    def add_arguments(self, parser):
        parser.add_argument('action', type=str, help='Action: import or export')
        parser.add_argument('--file', type=str, help='Path to the CSV file for import/export')
        parser.add_argument('--format', type=str, default='csv', help='File format: csv or json')

    def handle(self, *args, **options):
        action = options['action']
        file_path = options['file']
        file_format = options['format']
        
        if action == 'import':
            if not file_path:
                raise CommandError('File path is required for import')
            self.import_products(file_path, file_format)
        elif action == 'export':
            if not file_path:
                raise CommandError('File path is required for export')
            self.export_products(file_path, file_format)
        else:
            raise CommandError("Action must be 'import' or 'export'")

    def import_products(self, file_path, file_format):
        """Import products from a CSV/JSON file"""
        if file_format.lower() == 'csv':
            self.import_csv(file_path)
        elif file_format.lower() == 'json':
            self.import_json(file_path)
        else:
            raise CommandError(f"Unsupported format: {file_format}")

    def export_products(self, file_path, file_format):
        """Export products to a CSV/JSON file"""
        products = Product.objects.all()
        
        if file_format.lower() == 'csv':
            self.export_csv(products, file_path)
        elif file_format.lower() == 'json':
            self.export_json(products, file_path)
        else:
            raise CommandError(f"Unsupported format: {file_format}")

    def import_csv(self, file_path):
        """Import products from a CSV file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):  # Start from 2 to account for header
                try:
                    # Get or create category
                    category_name = row.get('category', '').strip()
                    category = None
                    if category_name:
                        category, created = Category.objects.get_or_create(
                            name=category_name,
                            defaults={'description': f'Auto-created for {category_name}'}
                        )
                        if created:
                            self.stdout.write(f'Created new category: {category_name}')
                    
                    # Handle tags
                    tags = row.get('tags', '').strip()
                    
                    # Create or update product
                    product, created = Product.objects.get_or_create(
                        sku=row['sku'].strip(),
                        defaults={
                            'name': row['name'].strip(),
                            'barcode': row.get('barcode', '').strip() or None,
                            'description': row.get('description', '').strip(),
                            'category': category,
                            'price': row['price'],
                            'wholesale_price': row.get('wholesale_price') or None,
                            'cost_price': row.get('cost_price') or None,
                            'min_wholesale_qty': row.get('min_wholesale_qty') or 1,
                            'tags': tags,
                            'is_active': row.get('is_active', 'true').lower() == 'true'
                        }
                    )
                    
                    if not created:
                        # Update existing product
                        product.name = row['name'].strip()
                        product.barcode = row.get('barcode', '').strip() or None
                        product.description = row.get('description', '').strip()
                        product.category = category
                        product.price = row['price']
                        product.wholesale_price = row.get('wholesale_price') or None
                        product.cost_price = row.get('cost_price') or None
                        product.min_wholesale_qty = row.get('min_wholesale_qty') or 1
                        product.tags = tags
                        product.is_active = row.get('is_active', 'true').lower() == 'true'
                        product.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'{"Created" if created else "Updated"} product: {product.name} (SKU: {product.sku})')
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error on row {row_num}: {str(e)}')
                    )

    def import_json(self, file_path):
        """Import products from a JSON file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
            for item in data:
                try:
                    # Get or create category
                    category_name = item.get('category', '').strip()
                    category = None
                    if category_name:
                        category, created = Category.objects.get_or_create(
                            name=category_name,
                            defaults={'description': f'Auto-created for {category_name}'}
                        )
                        if created:
                            self.stdout.write(f'Created new category: {category_name}')
                    
                    # Create or update product
                    product, created = Product.objects.get_or_create(
                        sku=item['sku'],
                        defaults={
                            'name': item['name'],
                            'barcode': item.get('barcode') or None,
                            'description': item.get('description', ''),
                            'category': category,
                            'price': item['price'],
                            'wholesale_price': item.get('wholesale_price') or None,
                            'cost_price': item.get('cost_price') or None,
                            'min_wholesale_qty': item.get('min_wholesale_qty') or 1,
                            'tags': item.get('tags', ''),
                            'is_active': item.get('is_active', True)
                        }
                    )
                    
                    if not created:
                        # Update existing product
                        product.name = item['name']
                        product.barcode = item.get('barcode') or None
                        product.description = item.get('description', '')
                        product.category = category
                        product.price = item['price']
                        product.wholesale_price = item.get('wholesale_price') or None
                        product.cost_price = item.get('cost_price') or None
                        product.min_wholesale_qty = item.get('min_wholesale_qty') or 1
                        product.tags = item.get('tags', '')
                        product.is_active = item.get('is_active', True)
                        product.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'{"Created" if created else "Updated"} product: {product.name} (SKU: {product.sku})')
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error importing product {item.get("name", "Unknown")}: {str(e)}')
                    )

    def export_csv(self, products, file_path):
        """Export products to a CSV file"""
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            fieldnames = [
                'name', 'sku', 'barcode', 'description', 'category', 
                'price', 'wholesale_price', 'cost_price', 'min_wholesale_qty',
                'effective_date', 'tags', 'is_active'
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in products:
                writer.writerow({
                    'name': product.name,
                    'sku': product.sku,
                    'barcode': product.barcode or '',
                    'description': product.description,
                    'category': product.category.name if product.category else '',
                    'price': product.price,
                    'wholesale_price': product.wholesale_price or '',
                    'cost_price': product.cost_price or '',
                    'min_wholesale_qty': product.min_wholesale_qty,
                    'effective_date': product.effective_date,
                    'tags': product.tags,
                    'is_active': product.is_active
                })
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully exported {products.count()} products to {file_path}')
        )

    def export_json(self, products, file_path):
        """Export products to a JSON file"""
        products_data = []
        for product in products:
            products_data.append({
                'name': product.name,
                'sku': product.sku,
                'barcode': product.barcode,
                'description': product.description,
                'category': product.category.name if product.category else None,
                'price': float(product.price),
                'wholesale_price': float(product.wholesale_price) if product.wholesale_price else None,
                'cost_price': float(product.cost_price) if product.cost_price else None,
                'min_wholesale_qty': product.min_wholesale_qty,
                'effective_date': product.effective_date.isoformat(),
                'image': str(product.image) if product.image else None,
                'tags': product.tags,
                'is_active': product.is_active,
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat()
            })
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(products_data, file, indent=2, ensure_ascii=False)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully exported {len(products_data)} products to {file_path}')
        )