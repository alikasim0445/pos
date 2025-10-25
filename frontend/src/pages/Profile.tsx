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
import MfaSettings from '../components/MfaSettings';

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
      <div className="flex justify-center items-center h-52">
        <CircularProgress />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex justify-center items-center h-52">
        <Typography variant="h6">Please log in to view profile</Typography>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Profile</h1>
        <p className="mt-2 text-gray-600">Manage your account information and preferences</p>
      </div>
      
      {error && (
        <Alert severity="error" className="mb-4">
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" className="mb-4">
          Profile updated successfully!
        </Alert>
      )}
      
      <Grid container spacing={6}>
        {/* Profile Sidebar */}
        <Grid item xs={12} md={4}>
          <Card className="shadow-lg">
            <CardContent className="text-center">
              {/* Profile Avatar */}
              <div className="flex justify-center mb-6">
                <Avatar 
                  sx={{ width: 120, height: 120, fontSize: 40, bgcolor: 'primary.main' }}
                  className="ring-4 ring-white shadow-lg"
                >
                  {(user.first_name?.charAt(0) || user.last_name?.charAt(0) || user.email?.charAt(0) || 'U').toUpperCase()}
                </Avatar>
              </div>
              
              {/* User Info */}
              <Typography variant="h6" className="font-semibold text-lg">
                {user.first_name} {user.last_name}
              </Typography>
              <Typography color="textSecondary" className="text-gray-600 mb-2">
                {user.email}
              </Typography>
              {user.profile?.role && (
                <Chip 
                  label={user.profile.role.replace('_', ' ').toUpperCase()} 
                  color="primary" 
                  className="mb-4"
                  sx={{ fontWeight: 600, textTransform: 'capitalize' }}
                />
              )}
              
              <Divider className="my-4" />
              
              {/* Account Information */}
              <div className="text-left">
                <Typography variant="subtitle1" className="font-medium mb-2">
                  Account Information
                </Typography>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Username:</span>
                    <span className="font-medium">{user.username}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Member since:</span>
                    <span className="font-medium">
                      {user.date_joined ? new Date(user.date_joined).toLocaleDateString() : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <Chip 
                      label={user.is_active ? "Active" : "Inactive"} 
                      color={user.is_active ? "success" : "error"} 
                      size="small"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Security Card */}
          <Card className="shadow-lg mt-6">
            <CardContent>
              <Typography variant="h6" className="font-semibold mb-4">
                Security
              </Typography>
              <Button 
                variant="outlined" 
                fullWidth
                onClick={() => alert('Change password functionality would be implemented here')}
                className="mt-2"
              >
                Change Password
              </Button>
            </CardContent>
          </Card>
          
          {/* MFA Settings */}
          {user?.profile?.role && (
            <MfaSettings userRole={user.profile.role} className="mt-6" />
          )}
        </Grid>
        
        {/* Profile Main Content */}
        <Grid item xs={12} md={8}>
          <Card className="shadow-lg">
            <CardContent>
              <div className="flex justify-between items-center mb-6">
                <Typography variant="h6" className="font-semibold text-lg">
                  Personal Information
                </Typography>
                <div>
                  {isEditing ? (
                    <div className="flex space-x-2">
                      <IconButton 
                        onClick={handleSaveClick} 
                        color="primary" 
                        disabled={loading}
                        title="Save"
                      >
                        {loading ? <CircularProgress size={20} /> : <SaveIcon />}
                      </IconButton>
                      <IconButton 
                        onClick={handleCancelClick} 
                        color="error" 
                        title="Cancel"
                      >
                        <CancelIcon />
                      </IconButton>
                    </div>
                  ) : (
                    <IconButton 
                      onClick={handleEditClick} 
                      color="primary"
                      title="Edit"
                    >
                      <EditIcon />
                    </IconButton>
                  )}
                </div>
              </div>
              
              <Grid container spacing={4}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="First Name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    variant={isEditing ? "outlined" : "filled"}
                    margin="normal"
                    InputLabelProps={isEditing ? undefined : { shrink: true }}
                    className={isEditing ? "bg-white" : "bg-gray-50"}
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
                    variant={isEditing ? "outlined" : "filled"}
                    margin="normal"
                    InputLabelProps={isEditing ? undefined : { shrink: true }}
                    className={isEditing ? "bg-white" : "bg-gray-50"}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Email Address"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    disabled={!isEditing}
                    variant={isEditing ? "outlined" : "filled"}
                    margin="normal"
                    InputLabelProps={isEditing ? undefined : { shrink: true }}
                    className={isEditing ? "bg-white" : "bg-gray-50"}
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
                    variant={isEditing ? "outlined" : "filled"}
                    margin="normal"
                    InputLabelProps={isEditing ? undefined : { shrink: true }}
                    className={isEditing ? "bg-white" : "bg-gray-50"}
                  />
                </Grid>
              </Grid>
              
              {user.profile?.role && (
                <>
                  <Divider className="my-6" />
                  <Typography variant="h6" className="font-semibold mb-4">
                    Role Information
                  </Typography>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="flex items-center mb-3">
                      <div className="mr-3 bg-blue-100 p-2 rounded-full">
                        <Chip 
                          label={user.profile.role.replace('_', ' ').toUpperCase()} 
                          color="primary"
                          size="small"
                          sx={{ fontWeight: 600 }}
                        />
                      </div>
                      <Typography variant="subtitle1" className="font-semibold">
                        {user.profile.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Typography>
                    </div>
                    <Typography variant="body2" className="text-gray-700">
                      {user.profile.role === 'super_admin' && "As a Super Admin, you have full system access and can manage all users and settings."}
                      {user.profile.role === 'admin' && "As an Admin, you can manage products, warehouses, pricing, and view reports."}
                      {user.profile.role === 'warehouse_manager' && "As a Warehouse Manager, you can manage received goods, stock adjustments, and transfers."}
                      {user.profile.role === 'store_manager' && "As a Store Manager, you can view store-level reports and approve transfers."}
                      {user.profile.role === 'cashier' && "As a Cashier, you can process sales, returns, and handle payments."}
                      {user.profile.role === 'accountant' && "As an Accountant, you can view financial reports and export data."}
                    </Typography>
                  </div>
                </>
              )}
              
              {isEditing && (
                <div className="mt-6 pt-4 border-t border-gray-200">
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
                  <Typography variant="caption" color="textSecondary" className="block mt-1">
                    Note: Account status can only be changed by administrators
                  </Typography>
                </div>
              )}
            </CardContent>
          </Card>
          
          {/* Super Admin - All Users View */}
          {user.profile?.role === 'super_admin' && (
            <Card className="shadow-lg mt-6">
              <CardContent>
                <div className="flex justify-between items-center mb-6">
                  <Typography variant="h6" className="font-semibold text-lg">
                    All Users
                  </Typography>
                  <Button 
                    variant="outlined" 
                    onClick={toggleShowAllUsers}
                    className="capitalize"
                  >
                    {showAllUsers ? 'Hide Users' : 'Show All Users'}
                  </Button>
                </div>
                
                {showAllUsers && (
                  <div>
                    {usersLoading ? (
                      <div className="flex justify-center my-6">
                        <CircularProgress />
                      </div>
                    ) : (
                      <Grid container spacing={3}>
                        {allUsers.map((u) => (
                          <Grid item xs={12} sm={6} md={4} key={u.id}>
                            <Card variant="outlined" className="p-4 hover:shadow-md transition-shadow">
                              <div className="flex items-center">
                                <Avatar 
                                  sx={{ width: 48, height: 48, fontSize: 18, bgcolor: 'secondary.main', mr: 3 }}
                                >
                                  {(u.first_name?.charAt(0) || u.last_name?.charAt(0) || u.email?.charAt(0) || 'U').toUpperCase()}
                                </Avatar>
                                <div className="flex-1 min-w-0">
                                  <Typography variant="subtitle2" className="font-medium truncate">
                                    {u.first_name} {u.last_name}
                                  </Typography>
                                  <Typography variant="body2" color="textSecondary" className="truncate">
                                    {u.username}
                                  </Typography>
                                  <div className="mt-2">
                                    <Chip 
                                      label={u.profile?.role?.replace('_', ' ').toUpperCase() || 'N/A'} 
                                      size="small"
                                      color={u.profile?.role === 'super_admin' ? 'error' : 'default'}
                                      className="capitalize"
                                    />
                                  </div>
                                </div>
                              </div>
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
        <div 
          className="fixed bottom-0 left-0 right-0 bg-white p-4 border-t border-gray-200 md:hidden"
        >
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Button 
                fullWidth 
                variant="outlined" 
                color="error" 
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
                startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <SaveIcon />}
              >
                {loading ? 'Saving...' : 'Save'}
              </Button>
            </Grid>
          </Grid>
        </div>
      )}
    </div>
  );
};

export default Profile;