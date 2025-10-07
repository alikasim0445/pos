import React, { useState } from 'react';
import {
  Container,
  Box,
  Avatar,
  Typography,
  TextField,
  Button,
  Link,
  FormControlLabel,
  Checkbox,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { register } from '../store/authSlice';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { useNavigate } from 'react-router-dom';
import PasswordInput from './PasswordInput';

const Register: React.FC = () => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState(''); // Add username field
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('cashier'); // Add role field with default
  const [acceptTerms, setAcceptTerms] = useState(false);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { isLoading, error } = useAppSelector((state) => state.auth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    
    if (!acceptTerms) {
      alert('You must accept the terms and conditions');
      return;
    }
    
    try {
      // Use email as username if username field is empty
      const userUsername = username || email;
      await dispatch(register({ email, password, password_confirm: confirmPassword, firstName, lastName, username: userUsername, role }));
      // Redirect to dashboard on successful registration
      navigate('/');
    } catch (err) {
      console.error('Registration failed:', err);
    }
  };

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

  return (
    <Container component="main" maxWidth="sm">
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
          Sign up
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3, width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {formatError(error)}
            </Alert>
          )}
          {/* All fields in vertical column without full width */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'center', width: '370px' }}>
            <TextField
              autoComplete="fname"
              name="firstName"
              required
              id="firstName"
              label="First Name"
              autoFocus
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              disabled={isLoading}
              sx={{ width: '100%' }}
            />
            <TextField
              required
              id="lastName"
              label="Last Name"
              name="lastName"
              autoComplete="lname"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              disabled={isLoading}
              sx={{ width: '100%' }}
            />
            <TextField
              required
              id="username"
              label="Username"
              name="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
              sx={{ width: '100%' }}
            />
            <TextField
              required
              id="email"
              label="Email Address"
              name="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              sx={{ width: '100%' }}
            />
            <PasswordInput
              label="Password"
              name="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              sx={{ width: '100%' }}
            />
            <PasswordInput
              label="Confirm Password"
              name="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isLoading}
              sx={{ width: '100%' }}
            />
            <FormControlLabel
              control={
                <Checkbox 
                  checked={acceptTerms}
                  onChange={(e) => setAcceptTerms(e.target.checked)}
                  name="acceptTerms" 
                  color="primary" 
                  disabled={isLoading}
                />
              }
              label={
                <span style={{ fontSize: '0.875rem' }}>
                  I agree to the <Link href="#" color="primary">Terms of Service</Link> and <Link href="#" color="primary">Privacy Policy</Link>
                </span>
              }
            />
          </Box>
          <Button
            type="submit"
            variant="contained"
            sx={{ mt: 3, mb: 2, width: '300px' }}
            disabled={isLoading}
            startIcon={isLoading && <CircularProgress size={20} />}
          >
            {isLoading ? 'Creating Account...' : 'Sign Up'}
          </Button>
          <Box sx={{ textAlign: 'center' }}>
            <Link href="/login" variant="body2">
              Already have an account? Sign in
            </Link>
          </Box>
        </Box>
      </Box>
    </Container>
  );
};

export default Register;