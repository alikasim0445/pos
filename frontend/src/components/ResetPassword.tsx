import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Avatar,
  Typography,
  TextField,
  Button,
  Link,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { passwordResetConfirm } from '../store/authSlice';
import { useNavigate, useParams } from 'react-router-dom';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import PasswordInput from './PasswordInput';

const ResetPassword: React.FC = () => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isValidToken, setIsValidToken] = useState(true);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { uidb64, token } = useParams<{ uidb64: string; token: string }>();
  const { isLoading, error } = useAppSelector((state) => state.auth);

  useEffect(() => {
    // You can add validation for the token here if needed
    // For now, we'll assume the token is valid if it's in the URL
    if (!uidb64 || !token) {
      setIsValidToken(false);
    }
  }, [uidb64, token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    
    try {
      await dispatch(passwordResetConfirm({ 
        uidb64, 
        token, 
        new_password: newPassword, 
        confirm_password: confirmPassword 
      })).unwrap();
      
      // Redirect to login after successful password reset
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      console.error('Password reset confirmation failed:', err);
    }
  };

  if (!isValidToken) {
    return (
      <Container component="main" maxWidth="xs">
        <Box
          sx={{
            marginTop: 8,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Avatar sx={{ m: 1, bgcolor: 'secondary.main' }}>
            <LockOutlinedIcon />
          </Avatar>
          <Typography component="h1" variant="h5">
            Invalid Reset Link
          </Typography>
          <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
            The password reset link is invalid or has expired. Please try resetting your password again.
          </Typography>
          <Button
            fullWidth
            variant="contained"
            sx={{ mt: 3 }}
            onClick={() => navigate('/forgot-password')}
          >
            Request New Link
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Avatar sx={{ m: 1, bgcolor: 'secondary.main' }}>
          <LockOutlinedIcon />
        </Avatar>
        <Typography component="h1" variant="h5">
          Reset Password
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {typeof error === 'string' ? error : JSON.stringify(error)}
            </Alert>
          )}
          <PasswordInput
            label="New Password"
            name="newPassword"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            disabled={isLoading}
          />
          <PasswordInput
            label="Confirm Password"
            name="confirmPassword"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={isLoading}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={isLoading}
            startIcon={isLoading && <CircularProgress size={20} />}
          >
            {isLoading ? 'Resetting...' : 'Reset Password'}
          </Button>
          <Grid container justifyContent="flex-end">
            <Grid item>
              <Link href="/login" variant="body2">
                Back to Sign In
              </Link>
            </Grid>
          </Grid>
        </Box>
      </Box>
    </Container>
  );
};

export default ResetPassword;