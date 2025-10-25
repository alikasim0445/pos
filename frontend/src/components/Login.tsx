import React, { useState } from 'react';
import {
  Container,
  Box,
  Avatar,
  Typography,
  TextField,
  Button,
  Grid,
  Link,
  FormControlLabel,
  Checkbox,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { login } from '../store/authSlice';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { useNavigate, useLocation } from 'react-router-dom';
import PasswordInput from './PasswordInput';
import apiClient from '../services/api';

const Login: React.FC = () => {
  const [email, setEmail] = useState(() => {
    // Retrieve email from localStorage if remember me was checked
    return localStorage.getItem('rememberedEmail') || '';
  });
  const [password, setPassword] = useState(() => {
    // Retrieve password from localStorage if remember me was checked
    return localStorage.getItem('rememberedPassword') || '';
  });
  const [rememberMe, setRememberMe] = useState(() => {
    // Check if remember me was previously selected
    return localStorage.getItem('rememberMe') === 'true';
  });
  const [showMfaDialog, setShowMfaDialog] = useState(false);
  const [mfaToken, setMfaToken] = useState('');
  const [mfaError, setMfaError] = useState('');
  const [isVerifyingMfa, setIsVerifyingMfa] = useState(false);
  const [loginRequiresMfa, setLoginRequiresMfa] = useState(false);
  const [tempUserDetails, setTempUserDetails] = useState({ userId: 0, username: '', email: '' });
  
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { isLoading, error } = useAppSelector((state) => state.auth);

  // Helper function to format error messages
  const formatError = (error: any): string => {
    if (typeof error === 'string') {
      return error;
    } else if (error && typeof error === 'object') {
      // For validation errors object like { field: ['error message'] }
      const errorFields = Object.keys(error);
      if (errorFields.length > 0) {
        return errorFields.map(field => {
          const messages = Array.isArray(error[field]) ? error[field] : [error[field]];
          return `${field}: ${messages.join(', ')}`;
        }).join('; ');
      }
      return JSON.stringify(error);
    }
    return 'An error occurred';
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const loginResult = await apiClient.post('/token/', { username: email, password });
      
      if (loginResult.data.requires_mfa) {
        // MFA is required
        setTempUserDetails({
          userId: loginResult.data.user_id,
          username: loginResult.data.username,
          email: loginResult.data.email,
        });
        setLoginRequiresMfa(true);
        setShowMfaDialog(true);
      } else {
        // Direct login (no MFA required)
        const result = await dispatch(login({ email, password })).unwrap();

        // Send token to service worker
        if (navigator.serviceWorker.controller) {
          navigator.serviceWorker.controller.postMessage({
            type: 'SET_AUTH_TOKEN',
            token: result.token,
          });
        }
        
        // Handle "Remember Me" functionality
        if (rememberMe) {
          // Save credentials to localStorage
          localStorage.setItem('rememberedEmail', email);
          localStorage.setItem('rememberedPassword', password);
          localStorage.setItem('rememberMe', 'true');
        } else {
          // Clear saved credentials if remember me is not checked
          localStorage.removeItem('rememberedEmail');
          localStorage.removeItem('rememberedPassword');
          localStorage.removeItem('rememberMe');
        }
        
        // Redirect to dashboard on successful login
        navigate(location.state?.from?.pathname || '/');
      }
    } catch (err: any) {
      console.error('Login failed:', err);
      // In case of error, clear saved credentials
      localStorage.removeItem('rememberedEmail');
      localStorage.removeItem('rememberedPassword');
      localStorage.removeItem('rememberMe');
    }
  };

  const handleMfaSubmit = async () => {
    setIsVerifyingMfa(true);
    setMfaError('');
    
    try {
      // Verify the MFA token
      const response = await apiClient.post('/mfa/verify/', {
        username: email, // using the email/username that was used for initial login
        token: mfaToken,
      });

      if (response.data.valid) {
        // If MFA is valid, now perform the actual login with email and password to get tokens
        const loginResult = await dispatch(login({ email, password })).unwrap();

        // Send token to service worker
        if (navigator.serviceWorker.controller) {
          navigator.serviceWorker.controller.postMessage({
            type: 'SET_AUTH_TOKEN',
            token: loginResult.token,
          });
        }

        // Handle "Remember Me" functionality
        if (rememberMe) {
          // Save credentials to localStorage
          localStorage.setItem('rememberedEmail', email);
          localStorage.setItem('rememberedPassword', password);
          localStorage.setItem('rememberMe', 'true');
        } else {
          // Clear saved credentials if remember me is not checked
          localStorage.removeItem('rememberedEmail');
          localStorage.removeItem('rememberedPassword');
          localStorage.removeItem('rememberMe');
        }
        
        setShowMfaDialog(false);
        setMfaToken('');
        
        // Redirect to dashboard on successful login
        navigate(location.state?.from?.pathname || '/');
      } else {
        setMfaError('Invalid MFA token. Please try again.');
      }
    } catch (err: any) {
      console.error('MFA verification failed:', err);
      setMfaError(err.response?.data?.error || 'MFA verification failed. Please try again.');
    } finally {
      setIsVerifyingMfa(false);
    }
  };

  const handleMfaCancel = () => {
    setShowMfaDialog(false);
    setMfaToken('');
    setMfaError('');
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
          Sign in
        </Typography>
        <Box component="form" onSubmit={handleLogin} sx={{ mt: 1 }}>
          {error && !loginRequiresMfa && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {formatError(error)}
            </Alert>
          )}
          <TextField
            margin="normal"
            required
            fullWidth
            id="email"
            label="Email Address or Username"
            name="email"
            autoComplete="email"
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isLoading || isVerifyingMfa}
          />
          <PasswordInput
            label="Password"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading || isVerifyingMfa}
          />
          <FormControlLabel
            control={
              <Checkbox 
                value="remember" 
                color="primary" 
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={isLoading || isVerifyingMfa}
              />
            }
            label="Remember me"
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={isLoading || isVerifyingMfa}
            startIcon={isLoading && <CircularProgress size={20} />}
          >
            {isLoading ? 'Signing In...' : 'Sign In'}
          </Button>
          <Grid container>
            <Grid item xs>
              <Link href="/forgot-password" variant="body2">
                Forgot password?
              </Link>
            </Grid>
            <Grid item>
              <Link href="/register" variant="body2">
                {"Don't have an account? Sign Up"}
              </Link>
            </Grid>
          </Grid>
        </Box>
      </Box>
      
      {/* MFA Dialog */}
      <Dialog open={showMfaDialog} onClose={handleMfaCancel} maxWidth="sm" fullWidth>
        <DialogTitle>Two-Factor Authentication</DialogTitle>
        <DialogContent>
          <Typography sx={{ mt: 2, mb: 2 }}>
            Please enter your authentication code from your authenticator app.
          </Typography>
          
          {mfaError && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {mfaError}
            </Alert>
          )}
          
          <TextField
            autoFocus
            margin="dense"
            label="Authentication Code"
            type="text"
            fullWidth
            variant="outlined"
            value={mfaToken}
            onChange={(e) => setMfaToken(e.target.value.replace(/\s/g, ''))}
            inputProps={{ maxLength: 6 }}
            disabled={isVerifyingMfa}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleMfaCancel} disabled={isVerifyingMfa}>Cancel</Button>
          <Button 
            onClick={handleMfaSubmit} 
            variant="contained" 
            disabled={isVerifyingMfa || mfaToken.length < 6}
          >
            {isVerifyingMfa ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Verifying...
              </>
            ) : 'Verify'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Login;