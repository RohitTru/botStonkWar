'use client';

import { useEffect, useState } from 'react';
import NotificationModal from './NotificationModal';
import { Box, Typography, Paper, Card, CardContent } from '@mui/material';

export default function UserDashboard({ user }: { user: any }) {
  const [latestTrade, setLatestTrade] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);
  const [userPositions, setUserPositions] = useState<{ symbol: string; shares: number }[]>([]);
  const [lastRespondedTradeId, setLastRespondedTradeId] = useState<number | null>(null);

  // Poll for latest trade recommendation
  useEffect(() => {
    let interval: any;
    const fetchLatest = async () => {
      try {
        const res = await fetch('/api/latest_trade_recommendation');
        if (!res.ok) return;
        const trade = await res.json();
        setLatestTrade(trade);
        // Check if user has responded
        const resp = await fetch(`/api/trade_acceptances?trade_id=${trade.id}&user_id=${user.id}`);
        const acceptances = await resp.json();
        if (!acceptances.length || lastRespondedTradeId !== trade.id) {
          setShowModal(true);
        } else {
          setShowModal(false);
        }
        setLastRespondedTradeId(acceptances.length ? trade.id : null);
        // Fetch user positions for SELL
        const posRes = await fetch(`/api/user_positions?user_id=${user.id}`);
        setUserPositions(await posRes.json());
      } catch (e) {
        // Ignore errors for now
      }
    };
    fetchLatest();
    interval = setInterval(fetchLatest, 15000);
    return () => clearInterval(interval);
  }, [user.id, lastRespondedTradeId]);

  const handleModalClose = () => setShowModal(false);
  const handleRespond = () => setShowModal(false);

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
        trade={latestTrade}
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
          textAlign: 'center',
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
          Welcome to Your Dashboard
        </Typography>
        <Typography variant="body1" sx={{ color: '#bdbddd' }}>
          This dashboard is currently under development. More features will be available soon.
        </Typography>
      </Paper>
    </Box>
  );
} 