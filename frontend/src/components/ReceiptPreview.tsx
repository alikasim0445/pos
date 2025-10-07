import React from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Divider,
  Button,
  Grid 
} from '@mui/material';
import { Print as PrintIcon } from '@mui/icons-material';
import { saleAPI } from '../services/api';

interface SaleLine {
  id: number;
  product_name: string;
  variant_name?: string;
  quantity: number;
  unit_price: string;
  total_price: string;
  discount_percent?: number;
}

interface Payment {
  id: number;
  payment_method: string;
  amount: string;
  reference: string;
  paid_at: string;
}

interface Sale {
  id: number;
  receipt_number: string;
  cashier: {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
  };
  customer?: {
    id: number;
    first_name: string;
    last_name: string;
    phone?: string;
  };
  warehouse: {
    id: number;
    name: string;
  };
  total_amount: string;
  tax_amount: string;
  discount_amount: string;
  payment_status: string;
  sale_date: string;
  lines: SaleLine[];
  payments: Payment[];
}

interface ReceiptPreviewProps {
  sale: Sale;
  onPrint?: () => void;
  onDownload?: () => void;
}

const ReceiptPreview: React.FC<ReceiptPreviewProps> = ({ 
  sale, 
  onPrint, 
  onDownload 
}) => {
  const handlePrint = () => {
    if (onPrint) {
      onPrint();
      return;
    }
    
    // Default print functionality
    window.print();
  };

  const handleDownload = async () => {
    if (onDownload) {
      onDownload();
      return;
    }
    
    // Default download functionality using backend endpoint
    try {
      const response = await saleAPI.downloadReceipt(sale.id);
      // Create a blob from the response data
      const blob = new Blob([response.data], { type: 'application/pdf' });
      // Create a download link
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', `receipt_${sale.receipt_number}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error downloading receipt:', error);
    }
  };

  return (
    <Card variant="outlined" sx={{ maxWidth: 400, mx: 'auto' }}>
      <CardContent>
        <Box textAlign="center" mb={2}>
          <Typography variant="h6" fontWeight="bold">
            ABC Store
          </Typography>
          <Typography variant="body2" color="textSecondary">
            123 Main Street, City, Country
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Tel: +1-234-567-890
          </Typography>
        </Box>

        <Divider sx={{ my: 1 }} />

        <Box mb={2}>
          <Typography variant="h6" align="center">
            RECEIPT
          </Typography>
          <Typography variant="body2">
            Receipt #: {sale.receipt_number}
          </Typography>
          <Typography variant="body2">
            Date: {new Date(sale.sale_date).toLocaleString()}
          </Typography>
          <Typography variant="body2">
            Cashier: {sale.cashier.first_name} {sale.cashier.last_name}
          </Typography>
          {sale.customer && (
            <Typography variant="body2">
              Customer: {sale.customer.first_name} {sale.customer.last_name}
              {sale.customer.phone && ` (${sale.customer.phone})`}
            </Typography>
          )}
        </Box>

        <Divider sx={{ my: 1 }} />

        <Box mb={2}>
          <Grid container spacing={0.5}>
            <Grid item xs={5}>
              <Typography variant="body2" fontWeight="bold">Item</Typography>
            </Grid>
            <Grid item xs={2}>
              <Typography variant="body2" fontWeight="bold" textAlign="right">Qty</Typography>
            </Grid>
            <Grid item xs={2.5}>
              <Typography variant="body2" fontWeight="bold" textAlign="right">Price</Typography>
            </Grid>
            <Grid item xs={2.5}>
              <Typography variant="body2" fontWeight="bold" textAlign="right">Total</Typography>
            </Grid>
          </Grid>

          {sale.lines.map((line, index) => (
            <Grid container key={index} spacing={0.5} sx={{ mt: 0.5 }}>
              <Grid item xs={5}>
                <Typography variant="body2">
                  {line.product_name}
                  {line.variant_name && ` (${line.variant_name})`}
                </Typography>
              </Grid>
              <Grid item xs={2}>
                <Typography variant="body2" textAlign="right">{line.quantity}</Typography>
              </Grid>
              <Grid item xs={2.5}>
                <Typography variant="body2" textAlign="right">${line.unit_price}</Typography>
              </Grid>
              <Grid item xs={2.5}>
                <Typography variant="body2" textAlign="right">${line.total_price}</Typography>
              </Grid>
            </Grid>
          ))}
        </Box>

        <Divider sx={{ my: 1 }} />

        <Box mb={1}>
          {sale.discount_amount && parseFloat(sale.discount_amount) > 0 && (
            <Grid container>
              <Grid item xs={6}>
                <Typography variant="body2">Subtotal:</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" textAlign="right">${sale.total_amount}</Typography>
              </Grid>
            </Grid>
          )}
          {sale.discount_amount && parseFloat(sale.discount_amount) > 0 && (
            <Grid container>
              <Grid item xs={6}>
                <Typography variant="body2">Discount:</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" textAlign="right">-${sale.discount_amount}</Typography>
              </Grid>
            </Grid>
          )}
          {sale.tax_amount && parseFloat(sale.tax_amount) > 0 && (
            <Grid container>
              <Grid item xs={6}>
                <Typography variant="body2">Tax:</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" textAlign="right">${sale.tax_amount}</Typography>
              </Grid>
            </Grid>
          )}
          <Grid container>
            <Grid item xs={6}>
              <Typography variant="body2" fontWeight="bold">TOTAL:</Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" fontWeight="bold" textAlign="right">${sale.total_amount}</Typography>
            </Grid>
          </Grid>
        </Box>

        <Divider sx={{ my: 1 }} />

        <Box mb={2}>
          <Typography variant="body2" fontWeight="bold">
            Payment Method(s):
          </Typography>
          {sale.payments.map((payment, index) => (
            <Typography key={index} variant="body2">
              {payment.payment_method}: ${payment.amount}
            </Typography>
          ))}
          <Typography variant="body2" fontWeight="bold">
            Status: {sale.payment_status}
          </Typography>
        </Box>

        <Divider sx={{ my: 1 }} />

        <Box textAlign="center" mt={2}>
          <Typography variant="body2" fontStyle="italic">
            Thank you for your business!
          </Typography>
          <Typography variant="body2">
            Powered by POS Management System
          </Typography>
        </Box>

        <Box display="flex" gap={1} mt={2}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<PrintIcon />}
            size="small"
            fullWidth
            onClick={handlePrint}
          >
            Print
          </Button>
          <Button
            variant="outlined"
            color="secondary"
            size="small"
            fullWidth
            onClick={handleDownload}
          >
            Download
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ReceiptPreview;