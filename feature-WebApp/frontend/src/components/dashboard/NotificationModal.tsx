import React, { useState } from 'react';
import { Box, Modal, Typography, Button, TextField, CircularProgress } from '@mui/material';

interface Trade {
  id: number;
  symbol: string;
  action: string;
  live_price?: number;
  status?: string;
  // Add more fields as needed
}

interface NotificationModalProps {
  open: boolean;
  trade: Trade | null;
  userId: number;
  onClose: () => void;
  onRespond: () => void;
  userPositions: { symbol: string; shares: number }[];
}

export default function NotificationModal({ open, trade, userId, onClose, onRespond, userPositions }: NotificationModalProps) {
  const [step, setStep] = useState<'choice' | 'input' | 'loading' | 'done'>('choice');
  const [allocation, setAllocation] = useState('');
  const [error, setError] = useState('');
  const [action, setAction] = useState<'ACCEPTED' | 'DENIED' | null>(null);
  const [userLiquidity, setUserLiquidity] = useState<number | null>(null);
  const [userShares, setUserShares] = useState<number>(0);

  React.useEffect(() => {
    // Fetch user liquidity and shares for the symbol
    if (trade && trade.action === 'BUY') {
      fetch('/api/auth/me').then(res => res.json()).then(data => {
        setUserLiquidity(data.user?.balance ?? null);
      });
    } else if (trade && trade.action === 'SELL') {
      const pos = userPositions.find(p => p.symbol === trade.symbol);
      setUserShares(pos ? pos.shares : 0);
    }
  }, [trade, userPositions]);

  if (!trade) return null;

  // Only show SELL if user owns shares
  if (trade.action === 'SELL') {
    const pos = userPositions.find(p => p.symbol === trade.symbol);
    if (!pos || pos.shares <= 0) return null;
  }

  const handleAccept = () => {
    setAction('ACCEPTED');
    setStep('input');
  };
  const handleDeny = () => {
    setAction('DENIED');
    submitResponse();
  };
  const submitResponse = async () => {
    setStep('loading');
    setError('');
    try {
      const body: any = {
        trade_id: trade.id,
        user_id: userId,
        status: action,
      };
      if (action === 'ACCEPTED') {
        if (trade.action === 'BUY') body.allocation_amount = parseFloat(allocation);
        if (trade.action === 'SELL') body.allocation_shares = parseInt(allocation);
      }
      const res = await fetch('/api/trade_acceptances', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('Failed to submit');
      setStep('done');
      onRespond();
    } catch (e: any) {
      setError(e.message || 'Error');
      setStep('choice');
    }
  };
  const handleInputSubmit = () => {
    if (!allocation || isNaN(Number(allocation)) || Number(allocation) <= 0) {
      setError('Enter a valid positive number');
      return;
    }
    if (trade.action === 'BUY') {
      if (userLiquidity !== null && Number(allocation) > userLiquidity) {
        setError('Cannot allocate more than your available liquidity');
        return;
      }
    }
    if (trade.action === 'SELL') {
      if (Number(allocation) > userShares) {
        setError('Cannot sell more shares than you own');
        return;
      }
    }
    setError('');
    submitResponse();
  };

  return (
    <Modal open={open} onClose={onClose}>
      <Box sx={{ p: 4, bgcolor: 'background.paper', borderRadius: 2, maxWidth: 400, mx: 'auto', mt: '10vh', boxShadow: 24 }}>
        <Typography variant="h6" gutterBottom>Trade Recommendation</Typography>
        <Typography>Symbol: <b>{trade.symbol}</b></Typography>
        <Typography>Action: <b>{trade.action}</b></Typography>
        <Typography>Price: ${trade.live_price ?? '-'}</Typography>
        <Typography>Status: {trade.status ?? '-'}</Typography>
        {step === 'choice' && (
          <Box mt={2} display="flex" gap={2}>
            <Button variant="contained" color="success" onClick={handleAccept}>Accept</Button>
            <Button variant="outlined" color="error" onClick={handleDeny}>Deny</Button>
          </Box>
        )}
        {step === 'input' && (
          <Box mt={2}>
            <TextField
              label={trade.action === 'BUY' ? 'Dollar Amount' : 'Shares to Sell'}
              value={allocation}
              onChange={e => setAllocation(e.target.value)}
              type="number"
              fullWidth
              size="small"
              sx={{ mb: 1 }}
            />
            {trade.action === 'BUY' && userLiquidity !== null && (
              <Typography variant="caption" sx={{ color: '#888' }}>
                Available liquidity: ${userLiquidity.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Typography>
            )}
            {trade.action === 'SELL' && (
              <Typography variant="caption" sx={{ color: '#888' }}>
                Shares owned: {userShares}
              </Typography>
            )}
            {error && <Typography color="error">{error}</Typography>}
            <Button variant="contained" onClick={handleInputSubmit} fullWidth>Submit</Button>
          </Box>
        )}
        {step === 'loading' && <CircularProgress sx={{ mt: 2 }} />}
        {step === 'done' && <Typography color="success.main" sx={{ mt: 2 }}>Response submitted!</Typography>}
        {error && step === 'choice' && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
      </Box>
    </Modal>
  );
} 