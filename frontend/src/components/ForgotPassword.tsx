import React, { useState } from 'react';
import {
  Container,
  Box,
  Paper,
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
import { passwordResetRequest } from '../store/authSlice';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';

const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const dispatch = useAppDispatch();
  const { isLoading, error } = useAppSelector((state) => state.auth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await dispatch(passwordResetRequest(email)).unwrap();
      setSuccessMessage('If your email exists in our system, you will receive a password reset link shortly.');
      setEmail('');
    } catch (err) {
      console.error('Password reset request failed:', err);
    }
  };

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
          Forgot Password
        </Typography>
        <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
          Enter your email address and we'll send you a link to reset your password.
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {typeof error === 'string' ? error : JSON.stringify(error)}
            </Alert>
          )}
          {successMessage && (
            <Alert severity="success" sx={{ width: '100%', mb: 2 }}>
              {successMessage}
            </Alert>
          )}
          <TextField
            margin="normal"
            required
            fullWidth
            id="email"
            label="Email Address"
            name="email"
            autoComplete="email"
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
            {isLoading ? 'Sending...' : 'Send Reset Link'}
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

export default ForgotPassword;