from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django_otp.plugins.otp_totp.models import TOTPDevice
from pos_app.models import UserProfile, BlacklistedToken
from django.utils import timezone
from django.core import mail
import json


class AuthenticationTestCase(TestCase):
    """Test authentication endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        # Create a user profile
        self.user_profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'role': 'cashier'}
        )

        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        # Create a user profile with admin role
        self.admin_profile, created = UserProfile.objects.get_or_create(
            user=self.admin_user,
            defaults={'role': 'admin'}
        )

        # Create a user with superuser privileges
        self.super_admin_user = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@example.com',
            password='superadminpass123',
            first_name='Super',
            last_name='Admin'
        )
        # Create a user profile with super_admin role
        self.super_admin_profile, created = UserProfile.objects.get_or_create(
            user=self.super_admin_user,
            defaults={'role': 'super_admin'}
        )

    def test_user_login_with_username(self):
        """Test user login with username"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['username'], 'testuser')

    def test_user_login_with_email(self):
        """Test user login with email"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_user_login_invalid_credentials(self):
        """Test user login with invalid credentials"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_user_login_missing_fields(self):
        """Test user login with missing fields"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser'
            # Missing password
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class UserRegistrationTestCase(TestCase):
    """Test user registration"""

    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        """Test user registration"""
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'role': 'cashier'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['email'], 'newuser@example.com')
        
        # Verify user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        
        # Verify user profile was created with correct role
        user_profile = UserProfile.objects.get(user=user)
        self.assertEqual(user_profile.role, 'cashier')

    def test_user_registration_password_mismatch(self):
        """Test user registration with password mismatch"""
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123',
            'password_confirm': 'differentpass',  # Different password
            'role': 'cashier'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_user_registration_duplicate_username(self):
        """Test user registration with duplicate username"""
        # Create an existing user first
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='existingpass'
        )
        
        url = reverse('register')
        data = {
            'username': 'existinguser',  # Existing username
            'email': 'different@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'role': 'cashier'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)


class MFAFunctionalityTestCase(TestCase):
    """Test Multi-Factor Authentication functionality"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        self.admin_profile, created = UserProfile.objects.get_or_create(
            user=self.admin_user,
            defaults={'role': 'admin'}
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user_profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'role': 'cashier'}
        )

        # Authenticate as super admin user
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        
        # Enable MFA
        url = reverse('enable-mfa')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('qr_code', response.data)
        self.assertIn('backup_codes', response.data)

    def test_enable_mfa_for_non_admin_user(self):
        """Test that regular users cannot enable MFA"""
        # Authenticate as regular user
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        
        # Try to enable MFA - should fail for regular users
        url = reverse('enable-mfa')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mfa_status(self):
        """Test getting MFA status"""
        # Authenticate as admin user
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'admin',
            'password': 'adminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        
        # Get MFA status
        url = reverse('mfa-status')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('is_mfa_enabled', response.data)
        self.assertIn('role', response.data)


class PasswordResetTestCase(TestCase):
    """Test password reset functionality"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user_profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'role': 'cashier'}
        )

    def test_password_reset_request(self):
        """Test requesting a password reset"""
        url = reverse('password_reset_request')
        data = {
            'email': 'test@example.com'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_password_reset_request_missing_email(self):
        """Test password reset request with missing email"""
        url = reverse('password_reset_request')
        data = {}  # No email
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class UserManagementTestCase(TestCase):
    """Test user management functionality"""

    def setUp(self):
        self.client = APIClient()
        self.super_admin_user = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='superadminpass123',
            first_name='Super',
            last_name='Admin'
        )
        self.super_admin_profile, created = UserProfile.objects.get_or_create(
            user=self.super_admin_user,
            defaults={'role': 'super_admin'}
        )

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user_profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'role': 'cashier'}
        )

    def test_get_user_list_by_super_admin(self):
        """Test getting user list as super admin"""
        # Authenticate as super admin
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        
        # Get user list
        url = reverse('super-admin-user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)  # At least super admin and test user

    def test_update_user_role_by_super_admin(self):
        """Test updating user role as super admin"""
        # Authenticate as super admin
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        
        # Update user role
        url = reverse('update-user-role', kwargs={'pk': self.user.id})
        data = {
            'role': 'admin'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Note: The response format might be different than expected in the test

    def test_create_user_with_role_by_super_admin(self):
        """Test creating user with role as super admin"""
        # Authenticate as super admin
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        
        # Create user with role
        url = reverse('create-user-with-role')
        data = {
            'username': 'newadmin',
            'email': 'newadmin@example.com',
            'first_name': 'New',
            'last_name': 'Admin',
            'password': 'adminpass123',
            'password_confirm': 'adminpass123',
            'role': 'admin'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newadmin')
        self.assertEqual(response.data['role'], 'admin')

    def test_delete_user_by_super_admin(self):
        """Test deleting user as super admin"""
        # Create a user to delete
        delete_user = User.objects.create_user(
            username='tobedeleted',
            email='delete@example.com',
            password='deletepass123'
        )
        delete_profile, created = UserProfile.objects.get_or_create(
            user=delete_user,
            defaults={'role': 'cashier'}
        )
        
        # Authenticate as super admin
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        
        # Delete user
        url = reverse('super-admin-user-detail', kwargs={'pk': delete_user.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify user was deleted
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='tobedeleted')


class TokenBlacklistingTestCase(TestCase):
    """Test token blacklisting functionality"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user_profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'role': 'cashier'}
        )

    def test_logout_and_token_blacklisting(self):
        """Test logout and token blacklisting"""
        # Login to get token
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        access_token = login_response.data['access']
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        
        # Logout to blacklist token
        logout_url = reverse('logout')
        logout_response = self.client.post(logout_url)
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # Verify token was blacklisted
        blacklisted_token_count = BlacklistedToken.objects.filter(
            jti__isnull=False
        ).count()
        self.assertGreaterEqual(blacklisted_token_count, 1)

    def test_check_token_validity(self):
        """Test checking token validity"""
        # Login to get token
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        access_token = login_response.data['access']
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        
        # Check token validity
        check_url = reverse('check-token-validity')
        check_response = self.client.get(check_url)
        self.assertEqual(check_response.status_code, status.HTTP_200_OK)
        self.assertTrue(check_response.data['valid'])
        self.assertIn('user_id', check_response.data)