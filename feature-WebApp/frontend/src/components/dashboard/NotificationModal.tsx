import React, { useState, useEffect } from 'react';
import { Box, Modal, Typography, Button, TextField, CircularProgress, Slider, Switch, FormControlLabel, Fade } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

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
  liquidity: number;
  setDisplayedLiquidity: (val: number) => void;
}

export default function NotificationModal({ open, trade, userId, onClose, onRespond, userPositions, liquidity, setDisplayedLiquidity }: NotificationModalProps) {
  const [step, setStep] = useState<'choice' | 'input' | 'loading' | 'done'>('choice');
  const [allocation, setAllocation] = useState('');
  const [error, setError] = useState('');
  const [action, setAction] = useState<'ACCEPTED' | 'DENIED' | null>(null);
  const [userLiquidity, setUserLiquidity] = useState<number | null>(null);
  const [userShares, setUserShares] = useState<number>(0);
  const [allocType, setAllocType] = useState<'dollar' | 'shares'>('dollar');
  const [sliderValue, setSliderValue] = useState<number>(0);
  const [livePrice, setLivePrice] = useState<number | null>(null);
  const [livePriceLoading, setLivePriceLoading] = useState(false);

  // Helper to reset allocation state
  const resetAllocation = () => {
    setAllocation('');
    setSliderValue(0);
    setError('');
  };

  React.useEffect(() => {
    if (trade && trade.action === 'BUY') {
      fetch('/api/auth/me').then(res => res.json()).then(data => {
        setUserLiquidity(data.user?.balance ?? null);
        setAllocType('dollar');
        setAllocation('1.00');
        setSliderValue(1);
        setError('');
      });
    } else if (trade && trade.action === 'SELL') {
      const pos = userPositions.find(p => p.symbol === trade.symbol);
      setUserShares(pos ? pos.shares : 0);
      setAllocType('shares');
      setAllocation('1');
      setSliderValue(1);
      setError('');
    }
    setStep('choice');
    setAction(null);
  }, [trade, userPositions, open]);

  // Fetch live price
  useEffect(() => {
    let interval: any;
    const fetchPrice = async () => {
      if (!trade?.symbol) return;
      setLivePriceLoading(true);
      try {
        const res = await fetch(`/api/live_price?symbol=${trade.symbol}`);
        const data = await res.json();
        if (data.price) setLivePrice(Number(data.price));
      } catch {}
      setLivePriceLoading(false);
    };
    if (open && trade?.symbol) {
      fetchPrice();
      interval = setInterval(fetchPrice, 15000);
    }
    return () => interval && clearInterval(interval);
  }, [open, trade?.symbol]);

  // Update displayed liquidity as allocation changes
  useEffect(() => {
    if (!open || !trade) return;
    let used = 0;
    if (trade.action === 'BUY' && allocType === 'dollar') {
      used = Number(allocation) || 0;
    } else if (trade.action === 'SELL' && allocType === 'shares' && livePrice) {
      used = (Number(allocation) || 0) * livePrice;
    }
    setDisplayedLiquidity(Math.max(0, liquidity - used));
  }, [allocation, allocType, livePrice, open, trade, liquidity, setDisplayedLiquidity]);

  if (!trade) return null;

  // Only show SELL if user owns shares
  if (trade.action === 'SELL') {
    const pos = userPositions.find(p => p.symbol === trade.symbol);
    if (!pos || pos.shares <= 0) return null;
  }

  // Handle toggle between dollar and shares
  const handleToggleAllocType = () => {
    if (trade?.action === 'BUY') {
      setAllocType((prev: 'dollar' | 'shares') => prev === 'dollar' ? 'shares' : 'dollar');
      resetAllocation();
    }
  };

  // Handle slider change
  const handleSliderChange = (_: any, val: number | number[]) => {
    const value = Array.isArray(val) ? val[0] : val;
    if (value < sliderMin || value > sliderMax) return;
    setSliderValue(value);
    setAllocation(String(value));
    setError('');
  };

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (!value || isNaN(Number(value)) || Number(value) < sliderMin || Number(value) > sliderMax) {
      setError('Enter a valid number in range.');
    } else {
      setError('');
    }
    setAllocation(value);
    setSliderValue(Number(value));
  };

  // Helper to validate allocation input
  const isValidAllocation = () => {
    if (!allocation) return false;
    if (allocType === 'dollar' && trade.action === 'BUY') {
      // Only allow positive numbers with up to 2 decimals
      if (!/^\d+(\.\d{1,2})?$/.test(allocation)) return false;
      const amount = Number(allocation);
      if (amount <= 0 || amount > (userLiquidity ?? 0)) return false;
      return true;
    }
    if (allocType === 'shares' && trade.action === 'SELL') {
      // Only allow positive whole numbers
      if (!/^\d+$/.test(allocation)) return false;
      const shares = Number(allocation);
      if (shares <= 0 || shares > userShares) return false;
      return true;
    }
    return false;
  };

  const handleAccept = () => {
    setAction('ACCEPTED');
    setStep('input');
    // Reset allocation when accepting
    if (trade.action === 'BUY') {
      setAllocation('1.00');
      setSliderValue(1);
    } else {
      setAllocation('1');
      setSliderValue(1);
    }
  };
  const handleDeny = () => {
    setAction('DENIED');
    submitResponse();
  };
  const submitResponse = async () => {
    if (!isValidAllocation()) {
      setError('Invalid allocation input.');
      setStep('input');
      return;
    }
    if (action === 'ACCEPTED') {
      let used = 0;
      if (allocType === 'dollar' && trade.action === 'BUY') used = Number(allocation) || 0;
      if (allocType === 'shares' && trade.action === 'SELL' && livePrice) used = (Number(allocation) || 0) * livePrice;
      if (used > liquidity) {
        setError('Cannot allocate more than your available liquidity.');
        setStep('input');
        return;
      }
      if (
        (allocType === 'dollar' && trade.action === 'BUY' && (!allocation || isNaN(Number(allocation)) || Number(allocation) <= 0)) ||
        (allocType === 'shares' && trade.action === 'SELL' && (!allocation || isNaN(Number(allocation)) || Number(allocation) <= 0))
      ) {
        setError('You must allocate a positive amount or number of shares.');
        setStep('input');
        return;
      }
    }
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
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Failed to submit');
      }
      setStep('done');
      onRespond();
    } catch (e: any) {
      setError(e.message || 'Error');
      setStep('choice');
    }
  };

  // Slider min/max
  const sliderMin = 1;
  const sliderMax = allocType === 'dollar' ? (userLiquidity ?? 1000) : Math.max(userShares, 1);
  const sliderStep = allocType === 'dollar' ? 0.01 : 1;

  return (
    <Modal open={open} onClose={onClose} closeAfterTransition>
      <Fade in={open}>
        <Box sx={{
          position: 'fixed',
          left: 0,
          right: 0,
          bottom: 0,
          mx: 'auto',
          mb: 6,
          bgcolor: 'rgba(255,255,255,0.97)',
          borderRadius: 4,
          maxWidth: 800,
          minWidth: 400,
          width: '95vw',
          boxShadow: 24,
          p: 5,
          border: '1.5px solid #e5e7eb',
          zIndex: 1300,
          transition: 'all 0.4s cubic-bezier(.4,0,.2,1)',
        }}>
          <Box sx={{ position: 'absolute', top: 16, right: 16, zIndex: 1400 }}>
            <Button onClick={onClose} sx={{ minWidth: 0, p: 0.5, color: '#888', background: 'transparent', '&:hover': { color: '#333' } }}>
              <CloseIcon />
            </Button>
          </Box>
          <Typography variant="h6" gutterBottom>Trade Recommendation</Typography>
          <Box display="flex" flexDirection="row" gap={3} mb={2}>
            <Box flex={1}>
              <Typography>Symbol: <b>{trade.symbol}</b></Typography>
              <Typography>Action: <b>{trade.action}</b></Typography>
              <Typography>Price: ${livePriceLoading ? '...' : (livePrice ?? trade.live_price ?? '-')}</Typography>
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
                      onChange={handleToggleAllocType}
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
                onChange={handleSliderChange}
                valueLabelDisplay="auto"
                sx={{ mb: 1 }}
              />
              <TextField
                label={allocType === 'dollar' ? 'Dollar Amount' : 'Shares'}
                value={allocation}
                onChange={handleInputChange}
                type="number"
                fullWidth
                size="small"
                sx={{ mb: 1 }}
              />
              {error && <Typography color="error">{error}</Typography>}
              <Button 
                variant="contained" 
                onClick={submitResponse} 
                fullWidth 
                disabled={!isValidAllocation() || !action}
              >
                Submit
              </Button>
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