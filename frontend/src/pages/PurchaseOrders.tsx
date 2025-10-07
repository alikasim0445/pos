import React, { useState, useEffect } from 'react';
import { purchaseOrderAPI, grnAPI } from '../services/api';
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

interface PurchaseOrderLine {
  id: number;
  product_name: string;
  variant_name?: string;
  ordered_qty: number;
  received_qty: number;
  unit_cost: number;
  total_price: number;
  discount_percent: number;
}

interface PurchaseOrder {
  id: number;
  po_number: string;
  supplier_name: string;
  warehouse_name: string;
  status: string;
  total_amount: number;
  order_date: string;
  expected_delivery_date: string;
  notes: string;
  lines: PurchaseOrderLine[];
}

interface GRNLine {
  id: number;
  product_name: string;
  ordered_qty: number;
  received_so_far: number;
  received_qty: number;
  condition: string;
}

interface GoodsReceivedNote {
  id: number;
  grn_number: string;
  po_number: string;
  received_by_name: string;
  received_date: string;
  notes: string;
  verified: boolean;
  verified_by_name: string;
  verified_date: string;
  lines: GRNLine[];
}

const PurchaseOrders: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([]);
  const [grns, setGrns] = useState<GoodsReceivedNote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        if (activeTab === 0) {
          const poResponse = await purchaseOrderAPI.getPurchaseOrders();
          setPurchaseOrders(poResponse.data);
        } else {
          const grnResponse = await grnAPI.getGRNs();
          setGrns(grnResponse.data);
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
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Purchase Orders & Receiving</h1>
      
      <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Purchase Orders" />
        <Tab label="Goods Received Notes" />
      </Tabs>
      
      {activeTab === 0 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Purchase Orders
          </Typography>
          
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>PO #</TableCell>
                  <TableCell>Supplier</TableCell>
                  <TableCell>Warehouse</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Total Amount</TableCell>
                  <TableCell>Order Date</TableCell>
                  <TableCell>Expected Delivery</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {purchaseOrders.map((po) => (
                  <TableRow key={po.id}>
                    <TableCell>{po.po_number}</TableCell>
                    <TableCell>{po.supplier_name}</TableCell>
                    <TableCell>{po.warehouse_name}</TableCell>
                    <TableCell>
                      <Chip 
                        label={po.status.replace('_', ' ').toUpperCase()} 
                        size="small" 
                        color={
                          po.status === 'received' ? 'success' :
                          po.status === 'ordered' || po.status === 'in_transit' ? 'info' :
                          po.status === 'pending' ? 'warning' :
                          po.status === 'cancelled' ? 'error' : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell align="right">${po.total_amount.toFixed(2)}</TableCell>
                    <TableCell>{new Date(po.order_date).toLocaleDateString()}</TableCell>
                    <TableCell>
                      {po.expected_delivery_date 
                        ? new Date(po.expected_delivery_date).toLocaleDateString() 
                        : 'N/A'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {purchaseOrders.length === 0 && (
            <Typography variant="body1" align="center" sx={{ mt: 2 }}>
              No purchase orders available.
            </Typography>
          )}
        </Box>
      )}
      
      {activeTab === 1 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Goods Received Notes
          </Typography>
          
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>GRN #</TableCell>
                  <TableCell>PO #</TableCell>
                  <TableCell>Received By</TableCell>
                  <TableCell>Received Date</TableCell>
                  <TableCell>Verified</TableCell>
                  <TableCell>Notes</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {grns.map((grn) => (
                  <TableRow key={grn.id}>
                    <TableCell>{grn.grn_number}</TableCell>
                    <TableCell>{grn.po_number}</TableCell>
                    <TableCell>{grn.received_by_name}</TableCell>
                    <TableCell>{new Date(grn.received_date).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Chip 
                        label={grn.verified ? "Verified" : "Pending"} 
                        size="small" 
                        color={grn.verified ? "success" : "warning"} 
                      />
                    </TableCell>
                    <TableCell>{grn.notes}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          
          {grns.length === 0 && (
            <Typography variant="body1" align="center" sx={{ mt: 2 }}>
              No goods received notes available.
            </Typography>
          )}
        </Box>
      )}
    </div>
  );
};

export default PurchaseOrders;