import React, { useState, useEffect } from 'react';
import { reportAPI } from '../services/api';
import { useAppSelector } from '../hooks/redux';
import { exportTableData } from '../utils/exportUtils';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Chip,
  Button,
  Grid,
} from '@mui/material';
import { Download as DownloadIcon } from '@mui/icons-material';

interface ProfitabilityReportItem {
  id: number;
  receipt_number: string;
  sale_date: string;
  total_revenue: number;
  total_cogs: number;
  profit: number;
  profit_margin: number;
}

interface ProfitabilityReportProps {
  filters: {
    startDate: string;
    endDate: string;
    warehouseId: string;
    categoryId: string;
  };
  canExport: boolean;
}

const ProfitabilityReport: React.FC<ProfitabilityReportProps> = ({ filters, canExport }) => {
  const [reportData, setReportData] = useState<ProfitabilityReportItem[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const params: any = {};
        if (filters.startDate) params.start_date = filters.startDate;
        if (filters.endDate) params.end_date = filters.endDate;
        
        const response = await reportAPI.getProfitabilityReport(params);
        setReportData(response.data.sales);
        setSummary(response.data.summary);
      } catch (err: any) {
        setError(err.message || 'Failed to load profitability report');
        console.error('Error loading profitability report:', err);
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchReport();
    }
  }, [filters, isAuthenticated]);

  const handleExport = (format: 'csv' | 'excel' | 'pdf') => {
    if (!reportData || reportData.length === 0) {
      setError('No data to export');
      return;
    }

    // Prepare data for export (add summary info as needed)
    const exportData = reportData.map(item => ({
      'Receipt #': item.receipt_number,
      'Date': new Date(item.sale_date).toLocaleDateString(),
      'Revenue': `${item.total_revenue.toFixed(2)}`,
      'COGS': `${item.total_cogs.toFixed(2)}`,
      'Profit': `${item.profit.toFixed(2)}`,
      'Margin %': `${item.profit_margin.toFixed(2)}%`,
    }));

    // Add summary as additional information
    const fileName = `profitability-report-${new Date().toISOString().split('T')[0]}.${format}`;
    exportTableData(exportData, format, fileName, 'Profitability Report');
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
    <Box>
      <Box mb={3}>
        <Grid container justifyContent="space-between" alignItems="center">
          <Grid item>
            <Typography variant="h6">Profitability Report Summary</Typography>
          </Grid>
          {canExport && (
            <Grid item>
              <Button 
                variant="outlined" 
                startIcon={<DownloadIcon />}
                onClick={() => handleExport('csv')}
                size="small"
                sx={{ mr: 1 }}
              >
                Export CSV
              </Button>
              <Button 
                variant="outlined" 
                startIcon={<DownloadIcon />}
                onClick={() => handleExport('excel')}
                size="small"
                sx={{ mr: 1 }}
              >
                Export Excel
              </Button>
              <Button 
                variant="outlined" 
                startIcon={<DownloadIcon />}
                onClick={() => handleExport('pdf')}
                size="small"
              >
                Export PDF
              </Button>
            </Grid>
          )}
        </Grid>
        {summary && (
          <Box display="flex" flexDirection="column" gap={1} mb={2}>
            <Box display="flex" gap={3}>
              <Chip label={`Total Revenue: ${summary.total_revenue.toFixed(2)}`} variant="outlined" />
              <Chip label={`Total COGS: ${summary.total_cogs.toFixed(2)}`} variant="outlined" />
              <Chip label={`Total Profit: ${summary.total_profit.toFixed(2)}`} variant="outlined" />
            </Box>
            <Box>
              <Chip label={`Overall Margin: ${summary.overall_profit_margin.toFixed(2)}%`} variant="outlined" />
              <Chip label={`Period: ${summary.date_range}`} variant="outlined" sx={{ ml: 1 }} />
            </Box>
          </Box>
        )}
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Receipt #</TableCell>
              <TableCell>Date</TableCell>
              <TableCell align="right">Revenue</TableCell>
              <TableCell align="right">COGS</TableCell>
              <TableCell align="right">Profit</TableCell>
              <TableCell align="right">Margin %</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {reportData.map((sale) => (
              <TableRow key={sale.id}>
                <TableCell>{sale.receipt_number}</TableCell>
                <TableCell>{new Date(sale.sale_date).toLocaleDateString()}</TableCell>
                <TableCell align="right">${sale.total_revenue.toFixed(2)}</TableCell>
                <TableCell align="right">${sale.total_cogs.toFixed(2)}</TableCell>
                <TableCell align="right">${sale.profit.toFixed(2)}</TableCell>
                <TableCell align="right">{sale.profit_margin.toFixed(2)}%</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {reportData.length === 0 && (
        <Typography variant="body1" align="center" sx={{ mt: 2 }}>
          No sales found for the selected criteria.
        </Typography>
      )}
    </Box>
  );
};

export default ProfitabilityReport;