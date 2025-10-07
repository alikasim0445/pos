import React, { useState } from 'react';
import QrScanner from 'react-qr-scanner';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button, 
  Box, 
  Alert,
  CircularProgress
} from '@mui/material';

interface BarcodeScannerProps {
  open: boolean;
  onClose: () => void;
  onScan: (data: string) => void;
  onError: (error: Error) => void;
}

const BarcodeScanner: React.FC<BarcodeScannerProps> = ({ 
  open, 
  onClose, 
  onScan, 
  onError 
}) => {
  const [error, setError] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(true);

  const handleScan = (result: any) => {
    if (result && result.text) {
      setIsScanning(false);
      onScan(result.text);
    }
  };

  const handleError = (err: any) => {
    setError(err.message);
    onError(err);
  };

  const handleRetry = () => {
    setError(null);
    setIsScanning(true);
  };

  const handleClose = () => {
    setIsScanning(false);
    onClose();
  };

  const previewStyle = {
    height: 300,
    width: '100%',
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>Scan Barcode</DialogTitle>
      <DialogContent dividers>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={300}>
          {isScanning ? (
            <Box width="100%" height="300px">
              <QrScanner
                onResult={handleScan}
                onError={handleError}
                style={previewStyle}
              />
              <Box mt={2} textAlign="center">
                <Alert severity="info">
                  Point your camera at the barcode to scan
                </Alert>
              </Box>
            </Box>
          ) : error ? (
            <Box textAlign="center">
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
              <Button variant="contained" onClick={handleRetry}>
                Retry
              </Button>
            </Box>
          ) : (
            <Box textAlign="center">
              <CircularProgress />
              <Box mt={2}>Processing scan...</Box>
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
      </DialogActions>
    </Dialog>
  );
};

export default BarcodeScanner;