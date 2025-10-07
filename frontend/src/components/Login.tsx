import React, { useState } from 'react';
import {
  Container,
  Box,
  Paper,
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
} from '@mui/material';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { login } from '../store/authSlice';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { useNavigate } from 'react-router-dom';
import PasswordInput from './PasswordInput';

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
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
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
      navigate('/');
    } catch (err) {
      console.error('Login failed:', err);
      // In case of error, clear saved credentials
      localStorage.removeItem('rememberedEmail');
      localStorage.removeItem('rememberedPassword');
      localStorage.removeItem('rememberMe');
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
          Sign in
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {formatError(error)}
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
          <PasswordInput
            label="Password"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
          />
          <FormControlLabel
            control={
              <Checkbox 
                value="remember" 
                color="primary" 
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={isLoading}
              />
            }
            label="Remember me"
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={isLoading}
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
    </Container>
  );
};

export default Login;