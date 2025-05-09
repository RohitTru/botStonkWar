'use client';

import React, { useEffect, useState } from 'react';
import NotificationModal from './NotificationModal';
import { Box, Typography, Paper, Card, CardContent, Button, Chip } from '@mui/material';
import TradeHistory from './TradeHistory';

export default function UserDashboard({ user }: { user: any }) {
  const [allTrades, setAllTrades] = useState<any[]>([]);
  const [activeTrade, setActiveTrade] = useState<any>(null);
  const [showModal, setShowModal] = useState(false);
  interface UserPosition {
    symbol: string;
    shares: number;
  }
  const [userPositions, setUserPositions] = useState<UserPosition[]>([]);
  const [lastRespondedTradeId, setLastRespondedTradeId] = useState<number | null>(null);
  // Pagination for expired trades
  const [expiredPage, setExpiredPage] = useState(1);
  const [expiredHasMore, setExpiredHasMore] = useState(true);
  const expiredPageSize = 20;
  const [displayedLiquidity, setDisplayedLiquidity] = useState(user?.balance ?? 0);
  // Equity and portfolio balance
  const [equity, setEquity] = useState(0);
  const [pendingAlloc, setPendingAlloc] = useState(0);
  const [portfolioBalance, setPortfolioBalance] = useState(0);

  useEffect(() => {
    setDisplayedLiquidity(user?.balance ?? 0);
  }, [user?.balance]);

  // Fetch equity and pending allocations
  useEffect(() => {
    const fetchEquity = async () => {
      try {
        const res = await fetch(`/api/user_equity?user_id=${user.id}`);
        if (!res.ok) return;
        const data = await res.json();
        setEquity(data.equity || 0);
        setPendingAlloc(data.pending_allocations || 0);
        // Always sum liquidity and equity for portfolio balance
        const liquidity = user?.balance ?? 0;
        const equityVal = data.equity || 0;
        setPortfolioBalance(Number(liquidity) + Number(equityVal));
      } catch (e) {
        // Ignore errors for now
      }
    };
    fetchEquity();
    const interval = setInterval(fetchEquity, 15000);
    return () => clearInterval(interval);
  }, [user.id, user?.balance]);

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
  // Only recommend SELL trades if user owns the symbol
  const userSymbols = new Set(userPositions.map((p: { symbol: string }) => p.symbol));
  const activeTrades = allTrades.filter((t: any) => {
    if (t.status !== 'PENDING' || t.is_expired) return false;
    if (t.action === 'SELL' && !userSymbols.has(t.symbol)) return false;
    return true;
  });
  const expiredTrades = allTrades.filter((t: any) => t.is_expired).slice(0, expiredPage * expiredPageSize);
  const respondedTrades = allTrades.filter((t: any) => t.status !== 'PENDING' && !t.is_expired && t.user_status !== 'PENDING');

  // Notification logic
  const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';
  const showSingleTradeModal = activeTrades.length === 1;
  // Only show multi trade card if NOT on /dashboard or /trades
  const showMultiTradeCard = activeTrades.length > 1 && !['/dashboard', '/trades'].includes(currentPath);

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
      {activeTrade && (
        <NotificationModal
          open={showModal}
          trade={activeTrade}
          userId={user.id}
          onClose={handleModalClose}
          onRespond={handleRespond}
          userPositions={userPositions}
          liquidity={user?.balance ?? 0}
          setDisplayedLiquidity={setDisplayedLiquidity}
        />
      )}
      {showMultiTradeCard && (
        <Card sx={{ mb: 3, background: '#282a36', color: '#fff', borderRadius: 2, p: 3, maxWidth: 500 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>New trades discovered</Typography>
          <Typography sx={{ mb: 2 }}>Multiple new trade recommendations are available. Please review them on the Trades page.</Typography>
          <Button variant="contained" color="primary" href="/trades">Go to Trades</Button>
        </Card>
      )}
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
      {/* Cards Row */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        {/* Liquidity Card */}
        <Card
          sx={{
            width: 140,
            background: 'linear-gradient(90deg, #7c5fff 0%, #6c47ff 100%)',
            boxShadow: 'none',
            borderRadius: 1.5,
            color: '#fff',
            border: '1px solid #7c5fff',
            p: 0,
          }}
        >
          <CardContent sx={{ textAlign: 'center', p: 1 }}>
            <Typography variant="caption" sx={{ color: '#e0d7ff', letterSpacing: 0.5, fontSize: 10 }} gutterBottom>
              Liquidity
            </Typography>
            <Typography variant="subtitle1" fontWeight={700} sx={{ color: '#fff', fontSize: 16 }}>
              ${displayedLiquidity?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Typography>
          </CardContent>
        </Card>
        {/* Equity Card */}
        <Card
          sx={{
            width: 140,
            background: 'linear-gradient(90deg, #00c6fb 0%, #005bea 100%)',
            boxShadow: 'none',
            borderRadius: 1.5,
            color: '#fff',
            border: '1px solid #00c6fb',
            p: 0,
          }}
        >
          <CardContent sx={{ textAlign: 'center', p: 1 }}>
            <Typography variant="caption" sx={{ color: '#b3e5fc', letterSpacing: 0.5, fontSize: 10 }} gutterBottom>
              Equity
            </Typography>
            <Typography variant="subtitle1" fontWeight={700} sx={{ color: '#fff', fontSize: 16 }}>
              ${equity?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Typography>
          </CardContent>
        </Card>
        {/* Portfolio Balance Card */}
        <Card
          sx={{
            width: 170,
            background: 'linear-gradient(90deg, #43e97b 0%, #38f9d7 100%)',
            boxShadow: 'none',
            borderRadius: 1.5,
            color: '#fff',
            border: '1px solid #43e97b',
            p: 0,
          }}
        >
          <CardContent sx={{ textAlign: 'center', p: 1 }}>
            <Typography variant="caption" sx={{ color: '#d0ffe6', letterSpacing: 0.5, fontSize: 10 }} gutterBottom>
              Portfolio Balance
            </Typography>
            <Typography variant="subtitle1" fontWeight={700} sx={{ color: '#fff', fontSize: 16 }}>
              ${(portfolioBalance)?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Typography>
          </CardContent>
        </Card>
      </Box>
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