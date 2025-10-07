from django.test import TestCase
from django.contrib.auth.models import User
from pos_app.models import UserProfile

class UserRegistrationTest(TestCase):
    def test_user_profile_creation(self):
        """Test that user profile is created with user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Check that user profile was created automatically
        self.assertTrue(hasattr(user, 'userprofile'))
        self.assertIsInstance(user.userprofile, UserProfile)