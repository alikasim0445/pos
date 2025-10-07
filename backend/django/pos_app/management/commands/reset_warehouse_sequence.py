from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Resets the primary key sequence for the pos_app_warehouse table.'

    def handle(self, *args, **options):
        self.stdout.write("Resetting primary key sequence for pos_app_warehouse table...")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT setval(pg_get_serial_sequence('pos_app_warehouse', 'id'), (SELECT MAX(id) FROM pos_app_warehouse));")
            self.stdout.write(self.style.SUCCESS('Successfully reset sequence for pos_app_warehouse.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))
