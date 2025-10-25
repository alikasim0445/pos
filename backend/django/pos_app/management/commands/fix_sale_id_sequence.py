from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix the ID sequences for Sale and Payment models to match highest used ID'

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