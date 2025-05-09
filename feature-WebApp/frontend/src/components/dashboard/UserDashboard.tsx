'use client';

import { useEffect, useState } from 'react';
import NotificationModal from './NotificationModal';
import { Box, Typography, Paper, Card, CardContent, Button, Chip } from '@mui/material';
import TradeHistory from './TradeHistory';

export default function UserDashboard({ user }: { user: any }) {
  const [allTrades, setAllTrades] = useState<any[]>([]);
  const [activeTrade, setActiveTrade] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);
  const [userPositions, setUserPositions] = useState<{ symbol: string; shares: number }[]>([]);
  const [lastRespondedTradeId, setLastRespondedTradeId] = useState<number | null>(null);
  // Pagination for expired trades
  const [expiredPage, setExpiredPage] = useState(1);
  const [expiredHasMore, setExpiredHasMore] = useState(true);
  const expiredPageSize = 20;

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
        const firstActive = trades.find((t: any) => t.status === 'PENDING' && !t.is_expired);
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
  const activeTrades = allTrades.filter(t => t.status === 'PENDING' && !t.is_expired);
  const expiredTrades = allTrades.filter(t => t.is_expired).slice(0, expiredPage * expiredPageSize);
  const respondedTrades = allTrades.filter(t => t.status !== 'PENDING' && !t.is_expired && t.user_status !== 'PENDING');

  const expiredLoadMore = () => {
    setExpiredPage(p => p + 1);
    if (expiredTrades.length < expiredPage * expiredPageSize) {
      setExpiredHasMore(false);
    }
  };

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
        <TradeHistory
          activeTrades={activeTrades}
          respondedTrades={respondedTrades}
          expiredTrades={expiredTrades}
          onAccept={trade => { setActiveTrade(trade); setShowModal(true); }}
          onDeny={trade => { setActiveTrade(trade); setShowModal(true); }}
          onShowModal={trade => { setActiveTrade(trade); setShowModal(true); }}
          expiredLoadMore={expiredLoadMore}
          expiredHasMore={expiredHasMore}
        />
      </Paper>
    </Box>
  );
} 