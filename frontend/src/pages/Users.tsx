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
  Alert as MuiAlert,
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
  Tooltip,
  Avatar,
  Stack,
  CardHeader,
} from '@mui/material';
import { 
  Add as AddIcon, 
  Edit as EditIcon, 
  Delete as DeleteIcon, 
  LockReset as ResetPasswordIcon, 
  Security as SecurityIcon,
  Person as PersonIcon 
} from '@mui/icons-material';
import { User } from '../types';

// Alert component for Snackbar - renamed to avoid conflict
const CustomAlert = React.forwardRef(function Alert(props: any, ref: any) {
  return <MuiAlert elevation={6} ref={ref} variant="filled" {...props} />;
});

interface UserFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (user: any) => void;
  initialData?: any;
  isEditing?: boolean;
}

const UserForm: React.FC<UserFormProps> = ({ open, onClose, onSubmit, initialData, isEditing }) => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    role: 'cashier',
    password: '',
    password_confirm: '',
    is_active: true,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (initialData) {
      setFormData({
        username: initialData.username || '',
        email: initialData.email || '',
        first_name: initialData.first_name || '',
        last_name: initialData.last_name || '',
        role: initialData.profile?.role || 'cashier',
        is_active: initialData.is_active !== undefined ? initialData.is_active : true,
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
        is_active: true,
        password: '',
        password_confirm: '',
      });
    }
    setErrors({});
  }, [initialData, open]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSelectChange = (name: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.username.trim()) newErrors.username = 'Username is required';
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    if (!formData.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) newErrors.email = 'Please enter a valid email address';
    
    if (!isEditing) {
      if (!formData.password) newErrors.password = 'Password is required';
      if (formData.password.length < 8) newErrors.password = 'Password must be at least 8 characters';
      if (formData.password !== formData.password_confirm) newErrors.password_confirm = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    try {
      // Prepare data for submission
      const submitData = {
        ...formData,
        id: initialData?.id
      };
      
      // Remove password fields if editing and no new password provided
      if (isEditing && !formData.password) {
        delete submitData.password;
        delete submitData.password_confirm;
      }
      
      await onSubmit(submitData);
      handleClose();
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setErrors({});
    setIsSubmitting(false);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {isEditing ? 'Edit User' : 'Create New User'}
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
                required
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
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth margin="dense">
                <InputLabel id="role-label">Role</InputLabel>
                <Select
                  labelId="role-label"
                  value={formData.role}
                  label="Role"
                  onChange={(e) => handleSelectChange('role', e.target.value)}
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
            
            {isEditing && (
              <Grid item xs={12}>
                <FormControl fullWidth margin="dense">
                  <InputLabel id="status-label">Status</InputLabel>
                  <Select
                    labelId="status-label"
                    value={formData.is_active}
                    label="Status"
                    onChange={(e) => handleSelectChange('is_active', e.target.value)}
                  >
                    <MenuItem value={true}>Active</MenuItem>
                    <MenuItem value={false}>Inactive</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                {isEditing ? 'Change Password (optional)' : 'Set Password'}
              </Typography>
            </Grid>
            
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
                helperText={errors.password || (isEditing ? 'Leave blank to keep current password' : '')}
                required={!isEditing}
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
                required={!isEditing}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button 
            type="submit" 
            variant="contained" 
            color="primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? <CircularProgress size={24} /> : (isEditing ? 'Update' : 'Create')}
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
  const [mfaResetDialogOpen, setMfaResetDialogOpen] = useState(false);
  const [passwordResetUserId, setPasswordResetUserId] = useState<number | null>(null);
  const [mfaResetUserId, setMfaResetUserId] = useState<number | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'warning' | 'info' });
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
      fetchUsers();
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to create user', 'error');
      console.error('Error creating user:', err);
      throw err; // Re-throw to handle in form
    }
  };

  const handleUpdateUser = async (userData: any) => {
    try {
      await userManagementService.updateUserProfile(userData.id, userData);
      showSnackbar('User updated successfully!', 'success');
      fetchUsers();
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to update user', 'error');
      console.error('Error updating user:', err);
      throw err; // Re-throw to handle in form
    }
  };

  const handleDeleteUser = async (userId: number) => {
    const userToDelete = users.find(u => u.id === userId);
    if (userToDelete?.id === currentUser?.id) {
      showSnackbar('You cannot delete your own account', 'error');
      return;
    }

    if (window.confirm(`Are you sure you want to delete user "${userToDelete?.username}"? This action cannot be undone.`)) {
      try {
        await userManagementService.deleteUser(userId);
        showSnackbar('User deleted successfully!', 'success');
        fetchUsers();
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

  const handleResetMfa = async () => {
    if (mfaResetUserId) {
      try {
        await userManagementService.resetUserMfa(mfaResetUserId);
        showSnackbar('MFA settings reset successfully!', 'success');
        setMfaResetDialogOpen(false);
        setMfaResetUserId(null);
      } catch (err: any) {
        showSnackbar(err.message || 'Failed to reset MFA settings', 'error');
        console.error('Error resetting MFA:', err);
      }
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' | 'warning') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const getRoleColor = (role: string) => {
    const colors: Record<string, "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning"> = {
      super_admin: 'error',
      admin: 'secondary',
      store_manager: 'primary',
      warehouse_manager: 'info',
      accountant: 'warning',
      cashier: 'default'
    };
    return colors[role] || 'default';
  };

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName?.charAt(0) || ''}${lastName?.charAt(0) || ''}`.toUpperCase();
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Card>
        <CardHeader
          title="User Management"
          action={
            <Fab 
              color="primary" 
              aria-label="add user"
              onClick={() => {
                setEditingUser(null);
                setIsFormOpen(true);
              }}
              size="medium"
            >
              <AddIcon />
            </Fab>
          }
        />
        <CardContent>
          {error && (
            <MuiAlert severity="error" sx={{ mb: 2 }}>
              {error}
            </MuiAlert>
          )}

          <TableContainer component={Paper} elevation={0}>
            <Table sx={{ minWidth: 650 }} aria-label="users table">
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Contact</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Joined</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                      <Typography color="text.secondary">
                        No users found
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((user) => (
                    <TableRow
                      key={user.id}
                      sx={{ 
                        '&:last-child td, &:last-child th': { border: 0 },
                        backgroundColor: user.id === currentUser?.id ? 'action.hover' : 'inherit'
                      }}
                    >
                      <TableCell>
                        <Stack direction="row" alignItems="center" spacing={2}>
                          <Avatar sx={{ bgcolor: 'primary.main' }}>
                            {getInitials(user.first_name, user.last_name)}
                          </Avatar>
                          <Box>
                            <Typography variant="subtitle2">
                              {user.first_name} {user.last_name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              @{user.username}
                            </Typography>
                          </Box>
                        </Stack>
                      </TableCell>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        <Chip 
                          label={user.profile?.role?.replace('_', ' ').toUpperCase() || 'N/A'} 
                          color={getRoleColor(user.profile?.role || '')}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        {user.date_joined ? new Date(user.date_joined).toLocaleDateString() : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={user.is_active ? "Active" : "Inactive"} 
                          color={user.is_active ? "success" : "error"} 
                          size="small"
                          variant={user.is_active ? "filled" : "outlined"}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Stack direction="row" spacing={1} justifyContent="center">
                          <Tooltip title="Edit User">
                            <IconButton 
                              color="primary" 
                              size="small"
                              onClick={() => {
                                setEditingUser(user);
                                setIsFormOpen(true);
                              }}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          
                          <Tooltip title={user.id === currentUser?.id ? "Cannot delete your own account" : "Delete User"}>
                            <span>
                              <IconButton 
                                color="error" 
                                size="small"
                                onClick={() => handleDeleteUser(user.id)}
                                disabled={user.id === currentUser?.id}
                              >
                                <DeleteIcon />
                              </IconButton>
                            </span>
                          </Tooltip>
                          
                          <Tooltip title="Reset Password">
                            <IconButton 
                              color="secondary" 
                              size="small"
                              onClick={() => {
                                setPasswordResetUserId(user.id);
                                setResetPasswordDialogOpen(true);
                              }}
                            >
                              <ResetPasswordIcon />
                            </IconButton>
                          </Tooltip>
                          
                          <Tooltip title="Reset MFA Settings">
                            <IconButton 
                              color="warning" 
                              size="small"
                              onClick={() => {
                                setMfaResetUserId(user.id);
                                setMfaResetDialogOpen(true);
                              }}
                            >
                              <SecurityIcon />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))
                )}
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
        isEditing={!!editingUser}
      />

      {/* Reset Password Dialog */}
      <Dialog open={resetPasswordDialogOpen} onClose={() => setResetPasswordDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Reset User Password</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="New Password"
            type="password"
            fullWidth
            variant="outlined"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            helperText="Password must be at least 8 characters long"
            error={newPassword.length > 0 && newPassword.length < 8}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetPasswordDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleResetPassword} 
            variant="contained" 
            color="primary"
            disabled={newPassword.length < 8}
          >
            Reset Password
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reset MFA Dialog */}
      <Dialog open={mfaResetDialogOpen} onClose={() => setMfaResetDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Reset MFA Settings</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to reset the two-factor authentication settings for this user? 
            This will disable MFA and remove all authentication devices.
          </Typography>
          <MuiAlert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone. The user will need to set up MFA again.
          </MuiAlert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMfaResetDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleResetMfa} 
            variant="contained" 
            color="warning"
          >
            Reset MFA
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <CustomAlert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </CustomAlert>
      </Snackbar>
    </Box>
  );
};

export default Users;