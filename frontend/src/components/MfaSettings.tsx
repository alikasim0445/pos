import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import { useAppSelector } from '../hooks/redux';
import apiClient from '../services/api';
import { Info as InfoIcon } from '@mui/icons-material';

interface MfaSettingsProps {
  userRole: string;
}

const MfaSettings: React.FC<MfaSettingsProps> = ({ userRole }) => {
  const { user } = useAppSelector((state) => state.auth);
  const [isMfaEnabled, setIsMfaEnabled] = useState(false);
  const [showSetupDialog, setShowSetupDialog] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [qrCodeData, setQrCodeData] = useState('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [mfaToken, setMfaToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [mfaStatus, setMfaStatus] = useState<{ is_mfa_enabled: boolean; role: string } | null>(null);

  // Check MFA status when component loads
  useEffect(() => {
    fetchMfaStatus();
  }, []);

  const fetchMfaStatus = async () => {
    try {
      const response = await apiClient.get('/mfa/status/');
      setMfaStatus(response.data);
      setIsMfaEnabled(response.data.is_mfa_enabled);
    } catch (err) {
      console.error('Error fetching MFA status:', err);
      setError('Failed to fetch MFA status');
    }
  };

  const handleEnableMfa = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await apiClient.post('/mfa/enable/');
      
      setQrCodeData(response.data.qr_code);
      setBackupCodes(response.data.backup_codes);
      setShowSetupDialog(true);
      setSuccess(response.data.message);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to enable MFA');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmMfa = async () => {
    if (mfaToken.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await apiClient.post('/mfa/confirm/', { token: mfaToken });
      setIsMfaEnabled(true);
      setShowSetupDialog(false);
      setShowConfirmDialog(false);
      setMfaToken('');
      setSuccess('MFA enabled successfully!');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to confirm MFA');
    } finally {
      setLoading(false);
    }
  };

  const handleDisableMfa = async () => {
    if (!window.confirm('Are you sure you want to disable two-factor authentication?')) {
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await apiClient.post('/mfa/disable/');
      setIsMfaEnabled(false);
      setSuccess('MFA disabled successfully');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to disable MFA');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Two-Factor Authentication
          <Tooltip title="Two-factor authentication adds an extra layer of security to your account">
            <IconButton size="small" sx={{ ml: 1 }}>
              <InfoIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Typography>
        
        <Typography variant="body2" color="textSecondary" gutterBottom>
          {isMfaEnabled
            ? 'Two-factor authentication is currently enabled on your account.'
            : 'Two-factor authentication is currently disabled on your account. Enable it for better security.'}
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert severity="success" sx={{ mt: 2, mb: 2 }}>
            {success}
          </Alert>
        )}
        
        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          {!isMfaEnabled ? (
            <Button 
              variant="contained" 
              color="primary"
              onClick={handleEnableMfa}
              disabled={loading || (userRole !== 'super_admin' && userRole !== 'admin')}
            >
              {loading ? <CircularProgress size={20} sx={{ mr: 1 }} /> : null}
              {userRole !== 'super_admin' && userRole !== 'admin' 
                ? 'Not Required' 
                : loading ? 'Enabling...' : 'Enable MFA'}
            </Button>
          ) : (
            <Button 
              variant="outlined" 
              color="error"
              onClick={handleDisableMfa}
              disabled={loading}
            >
              {loading ? <CircularProgress size={20} sx={{ mr: 1 }} /> : null}
              {loading ? 'Disabling...' : 'Disable MFA'}
            </Button>
          )}
        </Box>
        
        {/* MFA Setup Dialog */}
        <Dialog open={showSetupDialog} onClose={() => setShowSetupDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Setup Two-Factor Authentication</DialogTitle>
          <DialogContent>
            <Typography variant="body1" sx={{ mt: 2, mb: 2 }}>
              Scan the QR code below with your authenticator app (like Google Authenticator, Authy, etc.).
            </Typography>
            
            {qrCodeData && (
              <Box sx={{ textAlign: 'center', mt: 2, mb: 2 }}>
                <img src={`data:image/png;base64,${qrCodeData}`} alt="MFA QR Code" style={{ maxWidth: '200px' }} />
              </Box>
            )}
            
            <Typography variant="body2" sx={{ mt: 2, mb: 2 }}>
              If you cannot scan the QR code, you can manually add the account using this code:
              {/* For now, don't show the secret for security; in a real app, you'd need to get it from the backend */}
            </Typography>
            
            <Typography variant="h6" sx={{ mt: 2, mb: 2, textAlign: 'center' }}>
              Backup Codes
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Save these backup codes in a secure place. You can use them to access your account if you lose your phone.
            </Typography>
            
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(2, 1fr)', 
              gap: 1, 
              mb: 2,
              backgroundColor: '#f5f5f5',
              p: 2,
              borderRadius: 1
            }}>
              {backupCodes.map((code, index) => (
                <Typography key={index} variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                  {code}
                </Typography>
              ))}
            </Box>
            
            <Typography variant="h6" sx={{ mt: 2, mb: 2, textAlign: 'center' }}>
              Confirm Setup
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Enter the 6-digit code from your authenticator app to confirm setup:
            </Typography>
            
            <TextField
              fullWidth
              label="Authentication Code"
              variant="outlined"
              value={mfaToken}
              onChange={(e) => setMfaToken(e.target.value.replace(/\D/g, '').slice(0, 6))}
              inputProps={{ maxLength: 6, inputMode: 'numeric', pattern: '[0-9]*' }}
              disabled={loading}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => {
              setShowSetupDialog(false);
              setShowConfirmDialog(false);
            }} disabled={loading}>Cancel</Button>
            <Button 
              onClick={handleConfirmMfa} 
              variant="contained" 
              disabled={loading || mfaToken.length < 6}
            >
              {loading ? <CircularProgress size={20} sx={{ mr: 1 }} /> : null}
              {loading ? 'Verifying...' : 'Confirm MFA'}
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default MfaSettings;