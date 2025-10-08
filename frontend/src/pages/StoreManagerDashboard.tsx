import React, { useState } from 'react';
import { useAppSelector } from '../hooks/redux';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Alert,
} from '@mui/material';
import TransferApproval from '../components/TransferApproval';
import TransferReport from '../components/TransferReport';

const StoreManagerDashboard: React.FC = () => {
  const { user } = useAppSelector((state) => state.auth);
  const [activeTab, setActiveTab] = useState(0);

  // Check if user has store manager role
  const hasStoreManagerRole = user?.profile?.role === 'store_manager' || 
                             user?.profile?.role === 'admin' || 
                             user?.profile?.role === 'super_admin';

  if (!hasStoreManagerRole) {
    return (
      <Box className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Alert severity="error">
          You do not have permission to access this page. Store Manager role or higher required.
        </Alert>
      </Box>
    );
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Store Manager Dashboard</h1>
        <p className="mt-2 text-gray-600">Manage store operations and approve transfers</p>
      </div>

      <Card className="shadow-lg">
        <CardContent>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={activeTab} onChange={handleTabChange}>
              <Tab label="Transfer Approvals" />
              <Tab label="Transfer Report" />
              <Tab label="Sales Report" />
              <Tab label="Inventory Report" />
            </Tabs>
          </Box>

          <Box className="mt-4">
            {activeTab === 0 && (
              <Box>
                <Typography variant="h6" className="font-semibold mb-4">
                  Transfer Approvals
                </Typography>
                <TransferApproval />
              </Box>
            )}
            
            {activeTab === 1 && (
              <Box>
                <Typography variant="h6" className="font-semibold mb-4">
                  Transfer Report
                </Typography>
                <TransferReport filters={{ startDate: '', endDate: '', warehouseId: '', categoryId: '' }} />
              </Box>
            )}
            
            {activeTab === 2 && (
              <Box>
                <Typography variant="h6" className="font-semibold mb-4">
                  Sales Report
                </Typography>
                <Alert severity="info">
                  Sales reporting functionality will be implemented here.
                </Alert>
              </Box>
            )}
            
            {activeTab === 3 && (
              <Box>
                <Typography variant="h6" className="font-semibold mb-4">
                  Inventory Report
                </Typography>
                <Alert severity="info">
                  Inventory reporting functionality will be implemented here.
                </Alert>
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>
    </div>
  );
};

export default StoreManagerDashboard;