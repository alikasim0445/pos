import React, { useState, useEffect } from 'react';
import { promotionAPI, couponAPI } from '../services/api';
import { useAppSelector } from '../hooks/redux';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';

interface Promotion {
  id: number;
  name: string;
  description: string;
  promotion_type: string;
  discount_value: number;
  start_date: string;
  end_date: string;
  is_active: boolean;
  is_valid: boolean;
  used_count: number;
  max_usage_count: number | null;
}

interface Coupon {
  id: number;
  code: string;
  coupon_type: string;
  discount_value: number;
  start_date: string;
  end_date: string;
  is_active: boolean;
  is_valid: boolean;
  used_count: number;
  max_usage_count: number | null;
}

const Promotions: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [promotions, setPromotions] = useState<Promotion[]>([]);
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        if (activeTab === 0) {
          const promotionResponse = await promotionAPI.getPromotions();
          setPromotions(promotionResponse.data);
        } else {
          const couponResponse = await couponAPI.getCoupons();
          setCoupons(couponResponse.data);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load data');
        console.error('Error loading data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchData();
    }
  }, [activeTab, isAuthenticated]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Promotions & Discounts</h1>
      
      <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Promotions" />
        <Tab label="Coupons" />
      </Tabs>
      
      {activeTab === 0 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Promotions
          </Typography>
          
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Discount</TableCell>
                  <TableCell>Valid From</TableCell>
                  <TableCell>Valid To</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Usage</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {promotions.map((promo) => (
                  <TableRow key={promo.id}>
                    <TableCell>{promo.name}</TableCell>
                    <TableCell>{promo.description}</TableCell>
                    <TableCell>
                      <Chip 
                        label={promo.promotion_type.replace('_', ' ').toUpperCase()} 
                        size="small" 
                        variant="outlined" 
                      />
                    </TableCell>
                    <TableCell>
                      {promo.promotion_type === 'percentage' 
                        ? `${promo.discount_value}%` 
                        : `$${promo.discount_value.toFixed(2)}`}
                    </TableCell>
                    <TableCell>{new Date(promo.start_date).toLocaleDateString()}</TableCell>
                    <TableCell>{new Date(promo.end_date).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Chip 
                        label={promo.is_valid ? "Active" : "Inactive"} 
                        size="small" 
                        color={promo.is_valid ? "success" : "error"} 
                      />
                    </TableCell>
                    <TableCell>
                      {promo.used_count} / {promo.max_usage_count || '∞'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {promotions.length === 0 && (
            <Typography variant="body1" align="center" sx={{ mt: 2 }}>
              No promotions available.
            </Typography>
          )}
        </Box>
      )}
      
      {activeTab === 1 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Coupons
          </Typography>
          
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Code</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Discount</TableCell>
                  <TableCell>Valid From</TableCell>
                  <TableCell>Valid To</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Usage</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {coupons.map((coupon) => (
                  <TableRow key={coupon.id}>
                    <TableCell>
                      <Chip 
                        label={coupon.code} 
                        size="small" 
                        color="primary" 
                      />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={coupon.coupon_type.replace('_', ' ').toUpperCase()} 
                        size="small" 
                        variant="outlined" 
                      />
                    </TableCell>
                    <TableCell>
                      {coupon.coupon_type === 'percentage' 
                        ? `${coupon.discount_value}%` 
                        : `$${coupon.discount_value.toFixed(2)}`}
                    </TableCell>
                    <TableCell>{new Date(coupon.start_date).toLocaleDateString()}</TableCell>
                    <TableCell>{new Date(coupon.end_date).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Chip 
                        label={coupon.is_valid ? "Active" : "Inactive"} 
                        size="small" 
                        color={coupon.is_valid ? "success" : "error"} 
                      />
                    </TableCell>
                    <TableCell>
                      {coupon.used_count} / {coupon.max_usage_count || '∞'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {coupons.length === 0 && (
            <Typography variant="body1" align="center" sx={{ mt: 2 }}>
              No coupons available.
            </Typography>
          )}
        </Box>
      )}
    </div>
  );
};

export default Promotions;