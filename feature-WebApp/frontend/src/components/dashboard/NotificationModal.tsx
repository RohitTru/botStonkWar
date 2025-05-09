import React, { useState } from 'react';
import { Box, Modal, Typography, Button, TextField, CircularProgress, Slider, Switch, FormControlLabel, Fade } from '@mui/material';

interface Trade {
  id: number;
  symbol: string;
  action: string;
  live_price?: number;
  status?: string;
  strategy_name?: string;
  expires_at?: string;
  reasoning?: string;
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
  const [allocType, setAllocType] = useState<'dollar' | 'shares'>('dollar');
  const [sliderValue, setSliderValue] = useState<number>(0);

  React.useEffect(() => {
    // Fetch user liquidity and shares for the symbol
    if (trade && trade.action === 'BUY') {
      fetch('/api/auth/me').then(res => res.json()).then(data => {
        setUserLiquidity(data.user?.balance ?? null);
        setSliderValue(0);
        setAllocType('dollar');
      });
    } else if (trade && trade.action === 'SELL') {
      const pos = userPositions.find(p => p.symbol === trade.symbol);
      setUserShares(pos ? pos.shares : 0);
      setSliderValue(0);
      setAllocType('shares');
    }
    setAllocation('');
    setError('');
    setStep('choice');
    setAction(null);
  }, [trade, userPositions, open]);

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
        if (allocType === 'dollar' && trade.action === 'BUY') body.allocation_amount = parseFloat(allocation);
        if (allocType === 'shares' && trade.action === 'SELL') body.allocation_shares = parseInt(allocation);
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
    if (allocType === 'dollar' && trade.action === 'BUY') {
      if (userLiquidity !== null && Number(allocation) > userLiquidity) {
        setError('Cannot allocate more than your available liquidity');
        return;
      }
    }
    if (allocType === 'shares' && trade.action === 'SELL') {
      if (Number(allocation) > userShares) {
        setError('Cannot sell more shares than you own');
        return;
      }
    }
    setError('');
    submitResponse();
  };

  // Slider min/max
  const sliderMin = 0;
  const sliderMax = allocType === 'dollar' ? (userLiquidity ?? 1000) : userShares;
  const sliderStep = allocType === 'dollar' ? 1 : 1;

  return (
    <Modal open={open} onClose={onClose} closeAfterTransition>
      <Fade in={open}>
        <Box sx={{
          position: 'fixed',
          left: 0,
          right: 0,
          bottom: 0,
          mx: 'auto',
          mb: 0,
          bgcolor: 'rgba(255,255,255,0.95)',
          borderRadius: '24px 24px 0 0',
          maxWidth: 600,
          minWidth: 340,
          width: '90vw',
          boxShadow: 24,
          p: 4,
          border: '1.5px solid #e5e7eb',
          zIndex: 1300,
          transition: 'all 0.4s cubic-bezier(.4,0,.2,1)',
        }}>
          <Typography variant="h6" gutterBottom>Trade Recommendation</Typography>
          <Box display="flex" flexDirection="row" gap={3} mb={2}>
            <Box flex={1}>
              <Typography>Symbol: <b>{trade.symbol}</b></Typography>
              <Typography>Action: <b>{trade.action}</b></Typography>
              <Typography>Price: ${trade.live_price ?? '-'}</Typography>
              <Typography>Status: {trade.status ?? '-'}</Typography>
            </Box>
            <Box flex={1}>
              <Typography>Strategy: <b>{trade.strategy_name ?? '-'}</b></Typography>
              <Typography>Expires: <b>{trade.expires_at ? new Date(trade.expires_at).toLocaleString() : '-'}</b></Typography>
              {trade.reasoning && <Typography variant="caption">Reason: {trade.reasoning}</Typography>}
            </Box>
          </Box>
          {step === 'choice' && (
            <Box mt={2} display="flex" gap={2}>
              <Button variant="contained" color="success" onClick={handleAccept}>Accept</Button>
              <Button variant="outlined" color="error" onClick={handleDeny}>Deny</Button>
            </Box>
          )}
          {step === 'input' && (
            <Box mt={2}>
              <Box display="flex" alignItems="center" gap={2} mb={1}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={allocType === 'dollar'}
                      onChange={() => setAllocType(allocType === 'dollar' ? 'shares' : 'dollar')}
                      color="primary"
                      disabled={trade.action === 'SELL'}
                    />
                  }
                  label={trade.action === 'BUY' ? (allocType === 'dollar' ? 'Dollar Amount' : 'Shares') : 'Shares'}
                />
                <Typography variant="caption" sx={{ color: '#888' }}>
                  {allocType === 'dollar' ? `Available: $${userLiquidity?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : `Shares owned: ${userShares}`}
                </Typography>
              </Box>
              <Slider
                value={sliderValue}
                min={sliderMin}
                max={sliderMax}
                step={sliderStep}
                onChange={(_, val) => {
                  setSliderValue(Number(val));
                  setAllocation(String(val));
                }}
                valueLabelDisplay="auto"
                sx={{ mb: 1 }}
              />
              <TextField
                label={allocType === 'dollar' ? 'Dollar Amount' : 'Shares'}
                value={allocation}
                onChange={e => {
                  setAllocation(e.target.value);
                  setSliderValue(Number(e.target.value));
                }}
                type="number"
                fullWidth
                size="small"
                sx={{ mb: 1 }}
              />
              {error && <Typography color="error">{error}</Typography>}
              <Button variant="contained" onClick={handleInputSubmit} fullWidth>Submit</Button>
            </Box>
          )}
          {step === 'loading' && <CircularProgress sx={{ mt: 2 }} />}
          {step === 'done' && <Typography color="success.main" sx={{ mt: 2 }}>Response submitted!</Typography>}
          {error && step === 'choice' && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
        </Box>
      </Fade>
    </Modal>
  );
} 