from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pos_app.models import UserProfile

class Command(BaseCommand):
    help = 'Make a user a super admin'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to make super admin')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            
            # Make user a super admin
            user.is_superuser = True
            user.is_staff = True
            user.save()
            
            # Update profile role
            profile, created = UserProfile.objects.get_or_create(user=user)
            old_role = profile.role
            profile.role = 'super_admin'
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully made {user.username} a super admin. '
                    f'Previous role: {old_role}'
                )
            )
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'User "{username}" does not exist'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error making user super admin: {str(e)}'
                )
            )