from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix the ID sequences for all models to match highest used ID'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Update the sequence for Sale to be one more than the current max ID
            cursor.execute("SELECT setval('pos_app_sale_id_seq', (SELECT COALESCE(MAX(id), 0) FROM pos_app_sale) + 1);")
            self.stdout.write(
                self.style.SUCCESS('Successfully updated sale ID sequence')
            )
            
            # Update the sequence for Payment to be one more than the current max ID
            cursor.execute("SELECT setval('pos_app_payment_id_seq', (SELECT COALESCE(MAX(id), 0) FROM pos_app_payment) + 1);")
            self.stdout.write(
                self.style.SUCCESS('Successfully updated payment ID sequence')
            )
            
            # Update the sequence for other models that might have the issue
            # Check if Inventory has the same issue
            try:
                cursor.execute("SELECT setval('pos_app_inventory_id_seq', (SELECT COALESCE(MAX(id), 0) FROM pos_app_inventory) + 1);")
                self.stdout.write(
                    self.style.SUCCESS('Successfully updated inventory ID sequence')
                )
            except:
                self.stdout.write(
                    self.style.WARNING('Inventory sequence does not exist or was not updated')
                )

            # Check if any other models need sequence updates
            try:
                cursor.execute("SELECT setval('pos_app_saleline_id_seq', (SELECT COALESCE(MAX(id), 0) FROM pos_app_saleline) + 1);")
                self.stdout.write(
                    self.style.SUCCESS('Successfully updated saleline ID sequence')
                )
            except:
                self.stdout.write(
                    self.style.WARNING('SaleLine sequence does not exist or was not updated')
                )

            try:
                cursor.execute("SELECT setval('pos_app_customer_id_seq', (SELECT COALESCE(MAX(id), 0) FROM pos_app_customer) + 1);")
                self.stdout.write(
                    self.style.SUCCESS('Successfully updated customer ID sequence')
                )
            except:
                self.stdout.write(
                    self.style.WARNING('Customer sequence does not exist or was not updated')
                )