from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from pos_app.models import UserProfile


class Command(BaseCommand):
    help = 'Set a user\'s role to super_admin'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int, help='ID of the user to update')
        parser.add_argument('role', type=str, help='Role to assign to the user')

    def handle(self, *args, **options):
        user_id = options['user_id']
        role = options['role']
        
        try:
            user = User.objects.get(id=user_id)
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated user {user.username} (ID: {user.id}) to role: {role}'
                )
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID {user_id} does not exist')
            )