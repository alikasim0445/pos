from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Set a common test password for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='password@123',
            help='Password to set for all users (default: password@123)'
        )

    def handle(self, *args, **options):
        password = options['password']
        updated_count = 0
        
        for user in User.objects.all():
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated password for user: {user.username}'
                )
            )
            updated_count += 1
            
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} users. '
                f'All passwords set to: {password}'
            )
        )