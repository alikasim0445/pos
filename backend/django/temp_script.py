from django.contrib.auth.models import User; from pos_app.models import UserProfile  
user = User.objects.get(username='lammii'); user.is_superuser = True; user.is_staff = True; user.save()  
profile, created = UserProfile.objects.get_or_create(user=user); profile.role = 'super_admin'; profile.save()  
print(f'Made {user.username} a super admin with role {profile.role}') 
