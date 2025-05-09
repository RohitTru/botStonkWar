'use client';

import { useEffect, useState } from 'react';
import NotificationModal from './NotificationModal';
import { Box, Typography, Paper, Card, CardContent, Button, Chip } from '@mui/material';

export default function UserDashboard({ user }: { user: any }) {
  const [allTrades, setAllTrades] = useState<any[]>([]);
  const [activeTrade, setActiveTrade] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);
  const [userPositions, setUserPositions] = useState<{ symbol: string; shares: number }[]>([]);
  const [lastRespondedTradeId, setLastRespondedTradeId] = useState<number | null>(null);

  // Poll for all trade recommendations for the user
  useEffect(() => {
    let interval: any;
    const fetchAll = async () => {
      try {
        const res = await fetch(`/api/user_trade_recommendations?user_id=${user.id}`);
        if (!res.ok) return;
        const trades = await res.json();
        setAllTrades(trades);
        // Find the first active, unresponded trade
        const firstActive = trades.find((t: any) => t.is_active);
        setActiveTrade(firstActive || null);
        setShowModal(!!firstActive);
        // Fetch user positions for SELL
        const posRes = await fetch(`/api/user_positions?user_id=${user.id}`);
        const positions = await posRes.json();
        setUserPositions(positions);
        setLastRespondedTradeId(firstActive ? null : lastRespondedTradeId);
      } catch (e) {
        // Ignore errors for now
      }
    };
    fetchAll();
    interval = setInterval(fetchAll, 15000);
    return () => clearInterval(interval);
  }, [user.id, lastRespondedTradeId]);

  const handleModalClose = () => setShowModal(false);
  const handleRespond = () => setShowModal(false);

  // Group trades
  const activeTrades = allTrades.filter(t => t.is_active);
  const expiredTrades = allTrades.filter(t => t.is_expired);
  const respondedTrades = allTrades.filter(t => !t.is_active && !t.is_expired && t.user_status !== 'PENDING');

  return (
    <Box
      sx={{
        p: 3,
        minHeight: '100vh',
        background: '#18191A',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'flex-start',
      }}
    >
      <NotificationModal
        open={showModal}
        trade={activeTrade}
        userId={user.id}
        onClose={handleModalClose}
        onRespond={handleRespond}
        userPositions={userPositions}
      />
      <Box
        sx={{
          width: '100%',
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          mb: 1,
          pr: 2,
        }}
      >
        <Typography sx={{ color: '#bdbddd', fontSize: 14 }}>
          Logged in as <b>{user.username}</b>
        </Typography>
      </Box>
      <Card
        sx={{
          width: 120,
          mb: 2,
          background: 'linear-gradient(90deg, #7c5fff 0%, #6c47ff 100%)',
          boxShadow: 'none',
          borderRadius: 1.5,
          color: '#fff',
          border: '1px solid #7c5fff',
          p: 0,
        }}
      >
        <CardContent sx={{ textAlign: 'center', p: 0.5 }}>
          <Typography variant="caption" sx={{ color: '#e0d7ff', letterSpacing: 0.5, fontSize: 10 }} gutterBottom>
            Liquidity
          </Typography>
          <Typography variant="subtitle1" fontWeight={700} sx={{ color: '#fff', fontSize: 14 }}>
            ${user?.balance?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </Typography>
        </CardContent>
      </Card>
      <Paper
        sx={{
          p: 4,
          background: '#232526',
          color: '#fff',
          borderRadius: 3,
          boxShadow: 'none',
          mt: 0,
          width: '100%',
          maxWidth: 1400,
        }}
      >
        <Typography variant="h4" component="h1" gutterBottom sx={{ color: '#fff' }}>
          Trade Recommendations
        </Typography>
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" sx={{ color: '#bdbddd', mb: 1 }}>Active</Typography>
          {activeTrades.length === 0 && <Typography sx={{ color: '#888' }}>No active trade recommendations.</Typography>}
          {activeTrades.map(trade => (
            <Paper key={trade.id} sx={{ mb: 2, p: 2, background: '#282a36', borderRadius: 2 }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography><b>{trade.symbol}</b> ({trade.action})</Typography>
                  <Typography variant="caption">Strategy: {trade.strategy_name ?? '-'}</Typography>
                  <Typography variant="caption" sx={{ ml: 2 }}>Expires: {trade.expires_at ? new Date(trade.expires_at).toLocaleString() : '-'}</Typography>
                </Box>
                <Chip label="Active" color="success" />
              </Box>
              <Box mt={1} display="flex" gap={2}>
                <Button variant="contained" size="small" color="success" onClick={() => { setActiveTrade(trade); setShowModal(true); }}>Accept</Button>
                <Button variant="outlined" size="small" color="error" onClick={() => { setActiveTrade(trade); setShowModal(true); }}>Deny</Button>
              </Box>
            </Paper>
          ))}
        </Box>
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" sx={{ color: '#bdbddd', mb: 1 }}>Responded</Typography>
          {respondedTrades.length === 0 && <Typography sx={{ color: '#888' }}>No responded trades.</Typography>}
          {respondedTrades.map(trade => (
            <Paper key={trade.id} sx={{ mb: 2, p: 2, background: '#232526', borderRadius: 2 }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography><b>{trade.symbol}</b> ({trade.action})</Typography>
                  <Typography variant="caption">Strategy: {trade.strategy_name ?? '-'}</Typography>
                  <Typography variant="caption" sx={{ ml: 2 }}>Expires: {trade.expires_at ? new Date(trade.expires_at).toLocaleString() : '-'}</Typography>
                </Box>
                <Chip label={trade.user_status} color={trade.user_status === 'ACCEPTED' ? 'success' : 'error'} />
              </Box>
              <Box mt={1}>
                <Typography variant="caption">Allocated: {trade.allocation_amount ? `$${trade.allocation_amount}` : trade.allocation_shares ? `${trade.allocation_shares} shares` : '-'}</Typography>
              </Box>
            </Paper>
          ))}
        </Box>
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" sx={{ color: '#bdbddd', mb: 1 }}>Expired</Typography>
          {expiredTrades.length === 0 && <Typography sx={{ color: '#888' }}>No expired trades.</Typography>}
          {expiredTrades.map(trade => (
            <Paper key={trade.id} sx={{ mb: 2, p: 2, background: '#232526', borderRadius: 2, opacity: 0.6 }}>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography><b>{trade.symbol}</b> ({trade.action})</Typography>
                  <Typography variant="caption">Strategy: {trade.strategy_name ?? '-'}</Typography>
                  <Typography variant="caption" sx={{ ml: 2 }}>Expired: {trade.expires_at ? new Date(trade.expires_at).toLocaleString() : '-'}</Typography>
                </Box>
                <Chip label="Expired" color="default" />
              </Box>
            </Paper>
          ))}
        </Box>
      </Paper>
    </Box>
  );
} 