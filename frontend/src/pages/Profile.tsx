import React, { useState, useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import { userAPI } from '../services/api';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Avatar,
  Chip,
  Divider,
  IconButton,
  FormControlLabel,
  Switch,
} from '@mui/material';
import { User } from '../types';
import { Edit as EditIcon, Save as SaveIcon, Cancel as CancelIcon } from '@mui/icons-material';
import { userManagementService } from '../services/userManagementService';
import { isSuperAdmin } from '../utils/roleUtils';
import { updateUserInStore } from '../store/authSlice';

// Define the updateUserProfile action in the authSlice (we'll add this to the slice)
// For now, we'll implement the functionality in this component
const Profile: React.FC = () => {
  const dispatch = useAppDispatch();
  const { user, token, isLoading: authLoading, error: authError } = useAppSelector((state) => state.auth);
  const [profileData, setProfileData] = useState<User | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    username: '',
    is_active: true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [showAllUsers, setShowAllUsers] = useState(false);
  const [usersLoading, setUsersLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileData(user);
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        username: user.username || '',
        is_active: user.is_active !== undefined ? user.is_active : true,
      });
    }
  }, [user]);

  // Fetch all users if current user is Super Admin
  useEffect(() => {
    if (user && isSuperAdmin(user)) {
      fetchAllUsers();
    }
  }, [user, showAllUsers]);

  const fetchAllUsers = async () => {
    if (!user || !isSuperAdmin(user)) return;
    
    try {
      setUsersLoading(true);
      const usersData = await userManagementService.getAllUsers();
      setAllUsers(usersData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch users');
      console.error('Error fetching users:', err);
    } finally {
      setUsersLoading(false);
    }
  };

  const handleEditClick = () => {
    setIsEditing(true);
  };

  const handleCancelClick = () => {
    setIsEditing(false);
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        username: user.username || '',
        is_active: user.is_active !== undefined ? user.is_active : true,
      });
    }
  };

  const handleSaveClick = async () => {
    if (!user) return;

    try {
      setLoading(true);
      setError(null);
      
      // Update user profile using the userAPI
      const response = await userAPI.updateUser(user.id, formData);
      const updatedUser = response.data;
      
      // Update the user in the store using the Redux action
      dispatch(updateUserInStore(updatedUser));
      
      // Update the user in component state
      setProfileData(updatedUser);
      setIsEditing(false);
      setSuccess(true);
      
      // Hide success message after 3 seconds
      setTimeout(() => {
        setSuccess(false);
      }, 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to update profile');
      console.error('Error updating profile:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const toggleShowAllUsers = () => {
    setShowAllUsers(!showAllUsers);
  };

  if (authLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (!user) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="200px">
        <Typography variant="h6">Please log in to view profile</Typography>
      </Box>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">User Profile</h1>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Profile updated successfully!
        </Alert>
      )}
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" flexDirection="column" alignItems="center" mb={3}>
                <Avatar 
                  sx={{ width: 100, height: 100, fontSize: 30, mb: 2, bgcolor: 'primary.main' }}
                >
                  {(user.first_name?.charAt(0) || user.last_name?.charAt(0) || user.email?.charAt(0) || 'U').toUpperCase()}
                </Avatar>
                <Typography variant="h6" align="center">
                  {user.first_name} {user.last_name}
                </Typography>
                <Typography color="textSecondary" variant="body2" align="center">
                  {user.email}
                </Typography>
                {user.profile?.role && (
                  <Chip 
                    label={user.profile.role.replace('_', ' ').toUpperCase()} 
                    color="primary" 
                    sx={{ mt: 1 }} 
                  />
                )}
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle1" gutterBottom>
                Account Information
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Username:</strong> {user.username}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Member since:</strong> {user.date_joined ? new Date(user.date_joined).toLocaleDateString() : 'N/A'}
              </Typography>
              <Typography variant="body2">
                <strong>Status:</strong> 
                <Chip 
                  label={user.is_active ? "Active" : "Inactive"} 
                  color={user.is_active ? "success" : "error"} 
                  size="small" 
                  sx={{ ml: 1 }}
                />
              </Typography>
            </CardContent>
          </Card>
          
          {/* Security Card */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Security
              </Typography>
              <Button 
                variant="outlined" 
                fullWidth
                onClick={() => alert('Change password functionality would be implemented here')}
              >
                Change Password
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h6">Profile Information</Typography>
                <Box>
                  {isEditing ? (
                    <>
                      <IconButton 
                        onClick={handleSaveClick} 
                        color="primary" 
                        disabled={loading}
                        title="Save"
                      >
                        <SaveIcon />
                      </IconButton>
                      <IconButton 
                        onClick={handleCancelClick} 
                        color="secondary" 
                        title="Cancel"
                      >
                        <CancelIcon />
                      </IconButton>
                    </>
                  ) : (
                    <IconButton 
                      onClick={handleEditClick} 
                      color="primary"
                      title="Edit"
                    >
                      <EditIcon />
                    </IconButton>
                  )}
                </Box>
              </Box>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="First Name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    variant={isEditing ? "outlined" : "standard"}
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Last Name"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    variant={isEditing ? "outlined" : "standard"}
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    variant={isEditing ? "outlined" : "standard"}
                    margin="normal"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Username"
                    name="username"
                    value={formData.username}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    variant={isEditing ? "outlined" : "standard"}
                    margin="normal"
                  />
                </Grid>
              </Grid>
              
              {user.profile?.role && (
                <>
                  <Divider sx={{ my: 3 }} />
                  <Typography variant="h6" gutterBottom>
                    Role Information
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Typography variant="body2">
                        <strong>Role:</strong> {user.profile.role.replace('_', ' ').toUpperCase()}
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2">
                        {user.profile.role === 'super_admin' && "As a Super Admin, you have full system access and can manage all users and settings."}
                        {user.profile.role === 'admin' && "As an Admin, you can manage products, warehouses, pricing, and view reports."}
                        {user.profile.role === 'warehouse_manager' && "As a Warehouse Manager, you can manage received goods, stock adjustments, and transfers."}
                        {user.profile.role === 'store_manager' && "As a Store Manager, you can view store-level reports and approve transfers."}
                        {user.profile.role === 'cashier' && "As a Cashier, you can process sales, returns, and handle payments."}
                        {user.profile.role === 'accountant' && "As an Accountant, you can view financial reports and export data."}
                      </Typography>
                    </Grid>
                  </Grid>
                </>
              )}
              
              {isEditing && (
                <Box mt={3}>
                  <FormControlLabel
                    control={
                      <Switch
                        name="is_active"
                        checked={formData.is_active}
                        onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                        disabled
                      />
                    }
                    label="Account Active"
                    title="Account status can only be changed by administrators"
                  />
                  <Typography variant="caption" color="textSecondary">
                    Note: Account status can only be changed by administrators
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
          
          {/* Super Admin - All Users View */}
          {user.profile?.role === 'super_admin' && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                  <Typography variant="h6">All Users</Typography>
                  <Button 
                    variant="outlined" 
                    onClick={toggleShowAllUsers}
                  >
                    {showAllUsers ? 'Hide Users' : 'Show All Users'}
                  </Button>
                </Box>
                
                {showAllUsers && (
                  <div>
                    {usersLoading ? (
                      <Box display="flex" justifyContent="center" my={3}>
                        <CircularProgress />
                      </Box>
                    ) : (
                      <Grid container spacing={2}>
                        {allUsers.map((u) => (
                          <Grid item xs={12} sm={6} md={4} key={u.id}>
                            <Card variant="outlined" sx={{ p: 2 }}>
                              <Box display="flex" alignItems="center">
                                <Avatar 
                                  sx={{ width: 40, height: 40, fontSize: 16, bgcolor: 'secondary.main', mr: 2 }}
                                >
                                  {(u.first_name?.charAt(0) || u.last_name?.charAt(0) || u.email?.charAt(0) || 'U').toUpperCase()}
                                </Avatar>
                                <Box>
                                  <Typography variant="subtitle2">
                                    {u.first_name} {u.last_name}
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary">
                                    {u.username}
                                  </Typography>
                                  <Chip 
                                    label={u.profile?.role?.replace('_', ' ').toUpperCase() || 'N/A'} 
                                    size="small"
                                    color={u.profile?.role === 'super_admin' ? 'error' : 'default'}
                                    sx={{ mt: 1 }}
                                  />
                                </Box>
                              </Box>
                            </Card>
                          </Grid>
                        ))}
                      </Grid>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
      
      {/* Action Buttons for Mobile */}
      {isEditing && (
        <Box 
          display={{ xs: 'block', md: 'none' }} 
          sx={{ 
            position: 'fixed', 
            bottom: 0, 
            left: 0, 
            right: 0, 
            bgcolor: 'background.paper', 
            p: 2, 
            borderTop: '1px solid #e0e0e0' 
          }}
        >
          <Grid container spacing={1}>
            <Grid item xs={6}>
              <Button 
                fullWidth 
                variant="outlined" 
                color="secondary" 
                onClick={handleCancelClick}
                startIcon={<CancelIcon />}
              >
                Cancel
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button 
                fullWidth 
                variant="contained" 
                color="primary" 
                onClick={handleSaveClick}
                disabled={loading}
                startIcon={<SaveIcon />}
              >
                {loading ? 'Saving...' : 'Save'}
              </Button>
            </Grid>
          </Grid>
        </Box>
      )}
    </div>
  );
};

export default Profile;