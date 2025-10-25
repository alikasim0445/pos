import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Divider,
  Chip,
  Collapse,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PointOfSaleIcon from '@mui/icons-material/PointOfSale';
import InventoryIcon from '@mui/icons-material/Inventory';
import WarehouseIcon from '@mui/icons-material/Warehouse';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import AssessmentIcon from '@mui/icons-material/Assessment';
import LocalOfferIcon from '@mui/icons-material/LocalOffer';
import AssignmentIcon from '@mui/icons-material/Assignment';
import ExitToAppIcon from '@mui/icons-material/ExitToApp';
import StoreIcon from '@mui/icons-material/Store';
import PeopleIcon from '@mui/icons-material/People';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { logout } from '../store/authSlice';


interface AppLayoutProps {
  children: React.ReactNode;
}

const drawerWidth = 280; // Wider drawer for better readability

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    main: true,
    additional: false,
    user: false,
  });
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  // Close mobile drawer when route changes
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const toggleSection = (section: string) => {
    setOpenSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/', permission: null },
    { text: 'Sales', icon: <PointOfSaleIcon />, path: '/sales', permission: 'view_sale' },
    { text: 'Products', icon: <InventoryIcon />, path: '/products', permission: 'view_product' },
    { text: 'Inventory', icon: <InventoryIcon />, path: '/inventory', permission: 'view_inventory' },
    { text: 'Customers', icon: <AccountCircleIcon />, path: '/customers', permission: 'view_customer' },
    { text: 'Warehouses', icon: <WarehouseIcon />, path: '/warehouses', permission: 'view_warehouse' },
    { text: 'Reports', icon: <AssessmentIcon />, path: '/reports', permission: 'view_sales_report' },
    { text: 'Promotions', icon: <LocalOfferIcon />, path: '/promotions', permission: 'view_promotion' },
    { text: 'Purchase Orders', icon: <AssignmentIcon />, path: '/purchase-orders', permission: 'view_purchaseorder' },
    { text: 'Reservations', icon: <AssignmentIcon />, path: '/reservations', permission: 'view_reservation' },
  ];

  const additionalMenuItems = [
    { text: 'Financial Reports', icon: <AssessmentIcon />, path: '/accountant' },
    { text: 'Store Operations', icon: <StoreIcon />, path: '/store-manager' },
    { text: 'User Management', icon: <PeopleIcon />, path: '/users' },
  ];

  const renderMenuItems = (items: any[], sectionKey: string) => (
    <Collapse in={openSections[sectionKey]} timeout="auto" unmountOnExit>
      <List component="div" disablePadding>
        {items.map((item) => (
          <ListItemButton 
            key={item.text}
            sx={{ pl: 4 }}
            onClick={() => navigate(item.path)}
            selected={location.pathname === item.path}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItemButton>
        ))}
      </List>
    </Collapse>
  );

  const drawer = (
    <div>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            POS System
          </Typography>
        </Box>
      </Toolbar>
      <Divider />
      
      {/* Main Navigation Section */}
      <List>
        <ListItemButton onClick={() => toggleSection('main')}>
          <ListItemText primary="Main Navigation" />
          {openSections.main ? <ExpandLess /> : <ExpandMore />}
        </ListItemButton>
        {renderMenuItems(menuItems, 'main')}
      </List>

      {/* Additional Navigation Items */}
      <Divider />
      <List>
        <ListItemButton onClick={() => toggleSection('additional')}>
          <ListItemText primary="Additional Tools" />
          {openSections.additional ? <ExpandLess /> : <ExpandMore />}
        </ListItemButton>
        {renderMenuItems(additionalMenuItems, 'additional')}
      </List>

      {/* User Section */}
      <Divider />
      <List>
        <ListItemButton onClick={() => toggleSection('user')}>
          <ListItemText primary="User" />
          {openSections.user ? <ExpandLess /> : <ExpandMore />}
        </ListItemButton>
        <Collapse in={openSections.user} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            <ListItemButton 
              sx={{ pl: 4 }}
              onClick={() => navigate('/profile')}
              selected={location.pathname === '/profile'}
            >
              <ListItemIcon>
                <AccountCircleIcon />
              </ListItemIcon>
              <ListItemText primary="Profile" />
            </ListItemButton>
            <ListItemButton 
              sx={{ pl: 4 }}
              onClick={handleLogout}
            >
              <ListItemIcon>
                <ExitToAppIcon />
              </ListItemIcon>
              <ListItemText primary="Logout" />
            </ListItemButton>
          </List>
        </Collapse>
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
          zIndex: (theme) => theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {getPageTitle(location.pathname)}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip 
              label={user?.profile?.role?.replace('_', ' ') || 'User'} 
              color="secondary"
              size="small"
              variant="outlined"
            />
            <Typography variant="body2">
              {user?.name || user?.email || 'User'}
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>
      
      {/* Navigation Drawer */}
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
        aria-label="navigation"
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              backgroundColor: '#f5f5f5'
            },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
              backgroundColor: '#f5f5f5'
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      
      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          backgroundColor: (theme) => theme.palette.background.default,
        }}
      >
        <Toolbar /> {/* Spacer for AppBar */}
        {children}
      </Box>
    </Box>
  );
};

// Helper function to get page title from path
const getPageTitle = (pathname: string): string => {
  const titles: { [key: string]: string } = {
    '/': 'Dashboard',
    '/sales': 'Sales',
    '/products': 'Products',
    '/warehouses': 'Warehouses',
    '/inventory': 'Inventory',
    '/customers': 'Customers',
    '/reports': 'Reports',
    '/promotions': 'Promotions',
    '/purchase-orders': 'Purchase Orders',
    '/accountant': 'Financial Reports',
    '/store-manager': 'Store Operations',
    '/users': 'User Management',
    '/profile': 'User Profile',
  };
  
  return titles[pathname] || 'POS Management System';
};

export default AppLayout;