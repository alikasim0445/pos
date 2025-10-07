import React, { useState, useEffect } from 'react';
import { useAppSelector } from '../hooks/redux';
import { userManagementService } from '../services/userManagementService';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Fab,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  FormControl,
  InputLabel,
  Select,
  Snackbar,
  SnackbarContent,
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, LockReset as ResetPasswordIcon } from '@mui/icons-material';
import { User } from '../types';

interface UserFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (user: any) => void;
  initialData?: any;
}

const UserForm: React.FC<UserFormProps> = ({ open, onClose, onSubmit, initialData }) => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    role: 'cashier',
    password: '',
    password_confirm: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (initialData) {
      setFormData({
        username: initialData.username || '',
        email: initialData.email || '',
        first_name: initialData.first_name || '',
        last_name: initialData.last_name || '',
        role: initialData.profile?.role || 'cashier',
        password: '',
        password_confirm: '',
      });
    } else {
      setFormData({
        username: '',
        email: '',
        first_name: '',
        last_name: '',
        role: 'cashier',
        password: '',
        password_confirm: '',
      });
    }
  }, [initialData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Simple validation
    const newErrors: Record<string, string> = {};
    if (!formData.username.trim()) newErrors.username = 'Username is required';
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    if (!initialData && !formData.password) newErrors.password = 'Password is required';
    if (!initialData && formData.password !== formData.password_confirm) newErrors.password_confirm = 'Passwords do not match';
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    onSubmit({
      ...formData,
      id: initialData?.id // Include ID if editing
    });
    handleClose();
  };

  const handleClose = () => {
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {initialData ? 'Edit User' : 'Create New User'}
      </DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                autoFocus
                margin="dense"
                name="first_name"
                label="First Name"
                type="text"
                fullWidth
                variant="outlined"
                value={formData.first_name}
                onChange={handleChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                margin="dense"
                name="last_name"
                label="Last Name"
                type="text"
                fullWidth
                variant="outlined"
                value={formData.last_name}
                onChange={handleChange}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                margin="dense"
                name="username"
                label="Username"
                type="text"
                fullWidth
                variant="outlined"
                value={formData.username}
                onChange={handleChange}
                error={!!errors.username}
                helperText={errors.username}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                margin="dense"
                name="email"
                label="Email"
                type="email"
                fullWidth
                variant="outlined"
                value={formData.email}
                onChange={handleChange}
                error={!!errors.email}
                helperText={errors.email}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth margin="dense">
                <InputLabel id="role-label">Role</InputLabel>
                <Select
                  labelId="role-label"
                  name="role"
                  value={formData.role}
                  label="Role"
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as string })}
                >
                  <MenuItem value="cashier">Cashier</MenuItem>
                  <MenuItem value="accountant">Accountant</MenuItem>
                  <MenuItem value="warehouse_manager">Warehouse Manager</MenuItem>
                  <MenuItem value="store_manager">Store Manager</MenuItem>
                  <MenuItem value="admin">Admin</MenuItem>
                  <MenuItem value="super_admin">Super Admin</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            {!initialData && (
              <>
                <Grid item xs={12} sm={6}>
                  <TextField
                    margin="dense"
                    name="password"
                    label="Password"
                    type="password"
                    fullWidth
                    variant="outlined"
                    value={formData.password}
                    onChange={handleChange}
                    error={!!errors.password}
                    helperText={errors.password}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    margin="dense"
                    name="password_confirm"
                    label="Confirm Password"
                    type="password"
                    fullWidth
                    variant="outlined"
                    value={formData.password_confirm}
                    onChange={handleChange}
                    error={!!errors.password_confirm}
                    helperText={errors.password_confirm}
                  />
                </Grid>
              </>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button type="submit" variant="contained" color="primary">
            {initialData ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

const Users: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [resetPasswordDialogOpen, setResetPasswordDialogOpen] = useState(false);
  const [passwordResetUserId, setPasswordResetUserId] = useState<number | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const { user: currentUser } = useAppSelector((state) => state.auth);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const usersData = await userManagementService.getAllUsers();
      setUsers(usersData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch users');
      console.error('Error fetching users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (userData: any) => {
    try {
      await userManagementService.createUserWithRole(userData);
      showSnackbar('User created successfully!', 'success');
      fetchUsers(); // Refresh the user list
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to create user', 'error');
      console.error('Error creating user:', err);
    }
  };

  const handleUpdateUser = async (userData: any) => {
    try {
      await userManagementService.updateUserProfile(userData.id, userData);
      showSnackbar('User updated successfully!', 'success');
      fetchUsers(); // Refresh the user list
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to update user', 'error');
      console.error('Error updating user:', err);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await userManagementService.deleteUser(userId);
        showSnackbar('User deleted successfully!', 'success');
        fetchUsers(); // Refresh the user list
      } catch (err: any) {
        showSnackbar(err.message || 'Failed to delete user', 'error');
        console.error('Error deleting user:', err);
      }
    }
  };

  const handleResetPassword = async () => {
    if (!newPassword || newPassword.length < 8) {
      showSnackbar('Password must be at least 8 characters long', 'error');
      return;
    }

    if (passwordResetUserId) {
      try {
        await userManagementService.resetUserPassword(passwordResetUserId, newPassword);
        showSnackbar('Password reset successfully!', 'success');
        setResetPasswordDialogOpen(false);
        setNewPassword('');
        setPasswordResetUserId(null);
      } catch (err: any) {
        showSnackbar(err.message || 'Failed to reset password', 'error');
        console.error('Error resetting password:', err);
      }
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' | 'warning') => {
    setSnackbar({ open: true, message, severity });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1">
          User Management
        </Typography>
        <Fab 
          color="primary" 
          aria-label="add"
          onClick={() => {
            setEditingUser(null);
            setIsFormOpen(true);
          }}
        >
          <AddIcon />
        </Fab>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          <TableContainer component={Paper}>
            <Table sx={{ minWidth: 650 }} aria-label="users table">
              <TableHead>
                <TableRow>
                  <TableCell>Username</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Joined</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((user) => (
                  <TableRow
                    key={user.id}
                    sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                  >
                    <TableCell component="th" scope="row">
                      {user.username}
                    </TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>{user.first_name} {user.last_name}</TableCell>
                    <TableCell>
                      <Chip 
                        label={user.profile?.role?.replace('_', ' ').toUpperCase() || 'N/A'} 
                        color={user.profile?.role === 'super_admin' ? 'error' : user.profile?.role === 'admin' ? 'secondary' : 'default'} 
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{user.date_joined ? new Date(user.date_joined).toLocaleDateString() : 'N/A'}</TableCell>
                    <TableCell>
                      <Chip 
                        label={user.is_active ? "Active" : "Inactive"} 
                        color={user.is_active ? "success" : "error"} 
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton 
                        color="primary" 
                        size="small"
                        onClick={() => {
                          setEditingUser(user);
                          setIsFormOpen(true);
                        }}
                        title="Edit User"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton 
                        color="error" 
                        size="small"
                        onClick={() => handleDeleteUser(user.id)}
                        disabled={user.id === currentUser?.id}
                        title={user.id === currentUser?.id ? "Cannot delete your own account" : "Delete User"}
                      >
                        <DeleteIcon />
                      </IconButton>
                      <IconButton 
                        color="secondary" 
                        size="small"
                        onClick={() => {
                          setPasswordResetUserId(user.id);
                          setResetPasswordDialogOpen(true);
                        }}
                        title="Reset Password"
                      >
                        <ResetPasswordIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* User Form Dialog */}
      <UserForm
        open={isFormOpen}
        onClose={() => {
          setIsFormOpen(false);
          setEditingUser(null);
        }}
        onSubmit={editingUser ? handleUpdateUser : handleCreateUser}
        initialData={editingUser || undefined}
      />

      {/* Reset Password Dialog */}
      <Dialog open={resetPasswordDialogOpen} onClose={() => setResetPasswordDialogOpen(false)}>
        <DialogTitle>Reset User Password</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            name="newPassword"
            label="New Password"
            type="password"
            fullWidth
            variant="outlined"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            helperText="Password must be at least 8 characters"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetPasswordDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleResetPassword} variant="contained" color="primary">
            Reset Password
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <SnackbarContent
          sx={{ 
            bgcolor: snackbar.severity === 'success' ? 'success.main' : 
                     snackbar.severity === 'error' ? 'error.main' : 
                     snackbar.severity === 'warning' ? 'warning.main' : 'info.main' 
          }}
          message={snackbar.message}
        />
      </Snackbar>
    </div>
  );
};

export default Users;