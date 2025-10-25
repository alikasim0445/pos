import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_static.models import StaticDevice
from django.contrib.auth import get_user_model
import json
import pyotp
import qrcode
import base64
from io import BytesIO
import secrets
from .models import UserProfile
from django.core.cache import cache
import time
import binascii

User = get_user_model()
logger = logging.getLogger(__name__)

def generate_valid_secret():
    """Generate a valid base32 secret"""
    return pyotp.random_base32()

def base32_to_hex(base32_secret):
    """Convert a base32 secret to hex, which is what django-otp expects"""
    import base64
    import binascii
    
    if not base32_secret:
        raise ValueError("Base32 secret cannot be empty")
    
    # Add proper padding to make length a multiple of 8
    # Calculate padding needed: we need to pad to the next multiple of 8
    padding_needed = (8 - len(base32_secret) % 8) % 8
    padded_secret = base32_secret.upper() + '=' * padding_needed
    
    # Decode the padded base32 secret to bytes
    secret_bytes = base64.b32decode(padded_secret)
    # Convert bytes to hexadecimal
    hex_secret = secret_bytes.hex()
    return hex_secret

def hex_to_base32(hex_secret):
    """Convert a hex secret back to base32 format"""
    import base64
    
    # Convert hex to bytes
    secret_bytes = bytes.fromhex(hex_secret)
    # Encode to base32
    base32_secret = base64.b32encode(secret_bytes).decode('utf-8').rstrip('=')
    return base32_secret

def validate_base32_secret(secret):
    """Validate if a secret is proper base32"""
    try:
        if not secret:
            return False
        # Add proper padding before validation
        padding_needed = (8 - len(secret) % 8) % 8
        padded_secret = secret.upper() + '=' * padding_needed
        # Try to decode it
        base64.b32decode(padded_secret)
        return True
    except (binascii.Error, TypeError, ValueError):
        return False

def generate_qr_code(device, email):
    """Generate a QR code for TOTP setup"""
    # Get the base32 secret from the device's hex key
    base32_secret = hex_to_base32(device.key)
    
    # Construct the TOTP URI manually using pyotp
    totp = pyotp.TOTP(base32_secret)
    totp_uri = totp.provisioning_uri(
        name=email,
        issuer_name="POS Management System"
    )
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str, totp_uri

def safe_totp_verification(secret, token, window=2):
    """Safely verify TOTP token with error handling"""
    try:
        if not validate_base32_secret(secret):
            return False
        
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)
    except Exception as e:
        logger.error(f"Error in TOTP verification: {str(e)}")
        return False

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enable_mfa(request):
    """Enable MFA for the user"""
    try:
        user = request.user
        user_profile, created = UserProfile.objects.get_or_create(user=user)

        # Only allow admins to enable MFA for themselves for this implementation
        if user_profile.role not in ['super_admin', 'admin']:
            return Response(
                {'error': 'MFA is only required for admin roles'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Delete any existing devices to ensure a fresh start
        TOTPDevice.objects.filter(user=user).delete()
        StaticDevice.objects.filter(user=user).delete()

        # Generate a valid base32 secret for the TOTP algorithm
        base32_secret = generate_valid_secret()
        
        # Convert base32 secret to hex format that django-otp expects
        hex_secret = base32_to_hex(base32_secret)
        
        # Create TOTP device with the hex secret for django-otp
        device = TOTPDevice.objects.create(
            user=user, 
            name='default',
            key=hex_secret,  # Use hex format for django-otp
            tolerance=2,  # Allow 60-second window (2 * 30s)
            confirmed=False  # Start unconfirmed until user verifies
        )
        
        # Generate QR code using the device's key
        qr_data, totp_uri = generate_qr_code(device, user.email)
        
        # Store backup codes temporarily in cache
        backup_codes = [secrets.token_urlsafe(12)[:8] for _ in range(10)]
        cache.set(f'mfa_backup_codes_{user.id}', backup_codes, timeout=300)  # 5 minutes
        
        logger.info(f"MFA setup initiated for user {user.username}. Secret validated: {validate_base32_secret(device.key)}")
        
        return Response({
            'qr_code': qr_data,
            'backup_codes': backup_codes,
            'message': 'Scan the QR code with your authenticator app to enable MFA'
        })
        
    except Exception as e:
        logger.error(f"Error enabling MFA for user {request.user.username}: {str(e)}")
        return Response(
            {'error': 'Failed to enable MFA. Please try again.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_mfa(request):
    """Confirm MFA setup by validating a token"""
    try:
        user = request.user
        token = request.data.get('token')
        
        logger.info(f"MFA confirmation attempt for user {user.username} with token '{token}'")

        if not token:
            logger.error("MFA confirmation failed: Token is required")
            return Response(
                {'error': 'Token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the TOTP device
        try:
            device = TOTPDevice.objects.get(user=user, name='default')
        except TOTPDevice.DoesNotExist:
            logger.error(f"MFA confirmation failed: No MFA device found for user {user.username}")
            return Response(
                {'error': 'No MFA device found. Please enable MFA first.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Found MFA device for user {user.username}: {device.name} (confirmed: {device.confirmed})")
        
        # Convert hex key back to base32 for validation
        try:
            base32_secret = hex_to_base32(device.key)
            is_valid_base32 = validate_base32_secret(base32_secret)
        except Exception:
            is_valid_base32 = False
            
        logger.info(f"Device secret valid: {is_valid_base32}")
        
        # Validate the base32 secret before using it
        if not is_valid_base32:
            logger.error(f"Invalid base32 secret in device: {device.key}")
            
            # Fix the invalid secret
            new_base32_secret = generate_valid_secret()
            new_hex_secret = base32_to_hex(new_base32_secret)
            device.key = new_hex_secret
            device.save()
            logger.info(f"Fixed invalid secret with new valid secret")
            
            return Response({
                'error': 'MFA setup was corrupted. Please scan the QR code again.',
                'requires_new_setup': True
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert hex key back to base32 for pyotp verification
        try:
            base32_secret = hex_to_base32(device.key)
            is_valid = safe_totp_verification(base32_secret, token, window=2)
        except Exception as e:
            logger.error(f"Error during TOTP verification: {str(e)}")
            is_valid = False
            
        logger.info(f"Token verification result for user {user.username}: {is_valid}")

        if is_valid:
            # Mark device as confirmed
            device.confirmed = True
            device.save()
            
            # Enable MFA for the user
            user_profile = UserProfile.objects.get(user=user)
            user_profile.is_mfa_enabled = True
            user_profile.mfa_secret = device.key
            user_profile.save()
            
            # Retrieve and save backup codes
            backup_codes = cache.get(f'mfa_backup_codes_{user.id}')
            if backup_codes:
                user_profile.backup_codes = json.dumps(backup_codes)
                user_profile.save()
                cache.delete(f'mfa_backup_codes_{user.id}')
            
            logger.info(f"MFA enabled successfully for user {user.username}")
            return Response({
                'message': 'MFA enabled successfully',
                'backup_codes': backup_codes
            })
        else:
            # Additional debugging: Try manual verification with window
            try:
                base32_secret = hex_to_base32(device.key)
                manual_verify = safe_totp_verification(base32_secret, token, window=2)
            except Exception:
                manual_verify = False
            logger.info(f"Manual verification with window 2: {manual_verify}")
            
            # Debug info
            try:
                base32_secret = hex_to_base32(device.key)
                if validate_base32_secret(base32_secret):
                    try:
                        totp = pyotp.TOTP(base32_secret)
                        current_token = totp.now()
                        logger.info(f"Current expected token: {current_token}")
                    except:
                        pass
            except:
                pass
            
            logger.error(f"MFA confirmation failed: Invalid token for user {user.username}")
            return Response(
                {'error': 'Invalid token. Please check the code and try again.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error during MFA confirmation: {str(e)}")
        return Response(
            {'error': 'MFA setup error. Please try setting up MFA again.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disable_mfa(request):
    """Disable MFA for the user"""
    try:
        user = request.user
        user_profile = UserProfile.objects.get(user=user)
        
        # Delete TOTP devices
        TOTPDevice.objects.filter(user=user).delete()
        
        # Delete static devices (backup codes)
        StaticDevice.objects.filter(user=user).delete()
        
        # Disable MFA in user profile
        user_profile.is_mfa_enabled = False
        user_profile.mfa_secret = None
        user_profile.backup_codes = None
        user_profile.save()
        
        # Clear any cached backup codes
        cache.delete(f'mfa_backup_codes_{user.id}')
        
        logger.info(f"MFA disabled for user {user.username}")
        
        return Response({
            'message': 'MFA disabled successfully'
        })
        
    except Exception as e:
        logger.error(f"Error disabling MFA for user {request.user.username}: {str(e)}")
        return Response(
            {'error': 'Failed to disable MFA. Please try again.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_mfa(request):
    """Reset MFA completely and start fresh"""
    try:
        user = request.user
        
        # Delete all MFA devices
        TOTPDevice.objects.filter(user=user).delete()
        StaticDevice.objects.filter(user=user).delete()
        
        # Reset user profile
        user_profile = UserProfile.objects.get(user=user)
        user_profile.is_mfa_enabled = False
        user_profile.mfa_secret = None
        user_profile.backup_codes = None
        user_profile.save()
        
        # Clear cache
        cache.delete(f'mfa_backup_codes_{user.id}')
        
        logger.info(f"MFA completely reset for user {user.username}")
        
        return Response({
            'message': 'MFA reset successfully. You can now set up MFA again.'
        })
        
    except Exception as e:
        logger.error(f"Error resetting MFA for user {request.user.username}: {str(e)}")
        return Response(
            {'error': 'Failed to reset MFA. Please try again.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def verify_mfa(request):
    """Verify MFA token during login"""
    try:
        username = request.data.get('username')
        token = request.data.get('token')
        backup_code = request.data.get('backup_code')
        
        logger.info(f"MFA verification attempt for username: {username}")
        
        if not username or not (token or backup_code):
            return Response(
                {'error': 'Username and token or backup code are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Invalid username or email'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if not hasattr(user, 'userprofile') or not user.userprofile.is_mfa_enabled:
            return Response(
                {'error': 'MFA not enabled for this user'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify using TOTP token
        if token:
            try:
                device = TOTPDevice.objects.get(user=user, name='default', confirmed=True)
                
                # Convert hex key back to base32 for validation and verification
                try:
                    base32_secret = hex_to_base32(device.key)
                    is_valid_base32 = validate_base32_secret(base32_secret)
                except Exception:
                    is_valid_base32 = False
                    
                if not is_valid_base32:
                    logger.error(f"Invalid secret during verification for user {user.username}")
                    return Response(
                        {'error': 'MFA configuration error. Please contact administrator.'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Use pyotp for verification since django-otp can cause hex errors
                try:
                    is_valid = safe_totp_verification(base32_secret, token, window=2)
                except Exception:
                    is_valid = False
                logger.info(f"TOTP verification for {username}: {is_valid}")
                
                if is_valid:
                    return Response({
                        'valid': True,
                        'user_id': user.id
                    })
            except TOTPDevice.DoesNotExist:
                pass
        
        # If token verification failed, check backup codes
        if backup_code and user.userprofile.backup_codes:
            try:
                backup_codes = json.loads(user.userprofile.backup_codes)
                if backup_code in backup_codes:
                    # Remove the used backup code
                    backup_codes.remove(backup_code)
                    user.userprofile.backup_codes = json.dumps(backup_codes)
                    user.userprofile.save()
                    logger.info(f"Backup code used for {username}")
                    return Response({
                        'valid': True,
                        'user_id': user.id
                    })
            except (json.JSONDecodeError, ValueError):
                pass
        
        logger.warning(f"Failed MFA verification for {username}")
        return Response(
            {'error': 'Invalid token or backup code'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
        
    except Exception as e:
        logger.error(f"Error during MFA verification: {str(e)}")
        return Response(
            {'error': 'MFA verification error. Please try again.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mfa_status(request):
    """Get the MFA status for the current user"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        return Response({
            'is_mfa_enabled': user_profile.is_mfa_enabled,
            'role': user_profile.role
        })
    except Exception as e:
        logger.error(f"Error getting MFA status for user {request.user.username}: {str(e)}")
        return Response(
            {'error': 'Failed to get MFA status'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def debug_secret(request):
    """Debug endpoint to check the current secret"""
    try:
        device = TOTPDevice.objects.get(user=request.user, name='default')
        
        # Test the secret by converting hex to base32
        try:
            base32_secret = hex_to_base32(device.key)
            secret_valid = validate_base32_secret(base32_secret)
        except Exception:
            base32_secret = ""
            secret_valid = False
            
        current_time = int(time.time())
        
        debug_info = {
            'secret_hex': device.key,
            'secret_base32': base32_secret,
            'secret_valid': secret_valid,
            'device_confirmed': device.confirmed,
            'device_tolerance': device.tolerance,
            'current_time_window': current_time // 30,
        }
        
        # Only try to generate tokens if secret is valid
        if secret_valid and base32_secret:
            try:
                totp = pyotp.TOTP(base32_secret)
                debug_info.update({
                    'current_token': totp.now(),
                    'previous_token': totp.at(current_time - 30),
                    'next_token': totp.at(current_time + 30),
                })
            except Exception as e:
                debug_info['token_generation_error'] = str(e)
        
        return Response(debug_info)
        
    except TOTPDevice.DoesNotExist:
        return Response({'error': 'No TOTP device found'}, status=400)
    except Exception as e:
        logger.error(f"Error in debug_secret: {str(e)}")
        return Response({'error': 'Debug endpoint error'}, status=500)

from .permissions import IsSuperAdmin

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def reset_user_mfa(request, user_id):
    """
    Super Admin specific endpoint to reset a user's MFA settings
    """
    try:
        from django.contrib.auth.models import User
        from .models import UserProfile, AuditLog
        
        user = User.objects.get(id=user_id)
        user_profile = getattr(user, 'userprofile', None)
        
        if not user_profile:
            return Response(
                {'error': 'User profile not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Disable MFA for the user
        user_profile.is_mfa_enabled = False
        user_profile.mfa_secret = None
        user_profile.backup_codes = None
        user_profile.save()
        
        # Remove any MFA devices for the user
        TOTPDevice.objects.filter(user=user).delete()
        StaticDevice.objects.filter(user=user).delete()
        
        # Clear cache
        cache.delete(f'mfa_backup_codes_{user.id}')
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='update',
            object_type='userprofile',
            object_id=user.id,
            object_repr=f"MFA settings reset for user {user.username}",
            notes=f"MFA reset by super admin {request.user.username}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'message': f'MFA settings reset successfully for user {user.username}'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error resetting user MFA: {str(e)}")
        return Response(
            {'error': 'Failed to reset user MFA'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )