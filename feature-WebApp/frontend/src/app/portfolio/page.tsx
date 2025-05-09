'use client';

import { useEffect, useState } from 'react';
import { Box, Typography, Card, CardContent, CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';

export default function PortfolioPage() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [equity, setEquity] = useState(0);
  const [pendingAlloc, setPendingAlloc] = useState(0);
  const [portfolioBalance, setPortfolioBalance] = useState(0);
  const [liquidity, setLiquidity] = useState(0);
  const [breakdown, setBreakdown] = useState<any>({});

  // Fetch user info
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await fetch('/api/auth/me');
        if (!response.ok) {
          window.location.href = '/login';
          return;
        }
        const data = await response.json();
        if (!data.user) throw new Error('No user data');
        setUser(data.user);
        setLiquidity(data.user.balance ?? 0);
      } catch (err: any) {
        setError('Failed to fetch user data');
      } finally {
        setLoading(false);
      }
    };
    fetchUserData();
  }, []);

  // Fetch equity and breakdown
  useEffect(() => {
    if (!user) return;
    let interval: any;
    const fetchEquity = async () => {
      try {
        const res = await fetch(`/api/user_equity?user_id=${user.id}`);
        if (!res.ok) return;
        const data = await res.json();
        setEquity(data.equity || 0);
        setPendingAlloc(data.pending_allocations || 0);
        setPortfolioBalance((user.balance ?? 0) + (data.equity || 0));
        setBreakdown(data.breakdown || {});
      } catch (e) {
        // Ignore errors for now
      }
    };
    fetchEquity();
    interval = setInterval(fetchEquity, 15000);
    return () => clearInterval(interval);
  }, [user]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" sx={{ background: '#18191A' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" sx={{ background: '#18191A' }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, minHeight: '100vh', background: '#18191A', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Box sx={{ width: '100%', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', mb: 1, pr: 2 }}>
        <Typography sx={{ color: '#bdbddd', fontSize: 14 }}>
          Logged in as <b>{user.username}</b>
        </Typography>
      </Box>
      {/* Cards Row */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        {/* Liquidity Card */}
        <Card sx={{ width: 140, background: 'linear-gradient(90deg, #7c5fff 0%, #6c47ff 100%)', boxShadow: 'none', borderRadius: 1.5, color: '#fff', border: '1px solid #7c5fff', p: 0 }}>
          <CardContent sx={{ textAlign: 'center', p: 1 }}>
            <Typography variant="caption" sx={{ color: '#e0d7ff', letterSpacing: 0.5, fontSize: 10 }} gutterBottom>
              Liquidity
            </Typography>
            <Typography variant="subtitle1" fontWeight={700} sx={{ color: '#fff', fontSize: 16 }}>
              ${liquidity?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Typography>
          </CardContent>
        </Card>
        {/* Equity Card */}
        <Card sx={{ width: 140, background: 'linear-gradient(90deg, #00c6fb 0%, #005bea 100%)', boxShadow: 'none', borderRadius: 1.5, color: '#fff', border: '1px solid #00c6fb', p: 0 }}>
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
        <Card sx={{ width: 170, background: 'linear-gradient(90deg, #43e97b 0%, #38f9d7 100%)', boxShadow: 'none', borderRadius: 1.5, color: '#fff', border: '1px solid #43e97b', p: 0 }}>
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
      {/* Holdings Table */}
      <Paper sx={{ p: 3, background: '#232526', color: '#fff', borderRadius: 3, boxShadow: 'none', mt: 0, width: '100%', maxWidth: 900 }}>
        <Typography variant="h5" component="h2" gutterBottom sx={{ color: '#fff', mb: 2 }}>
          Portfolio Holdings
        </Typography>
        <TableContainer component={Paper} sx={{ background: 'transparent', boxShadow: 'none' }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: '#bdbddd', fontWeight: 700, background: 'transparent' }}>Symbol</TableCell>
                <TableCell sx={{ color: '#bdbddd', fontWeight: 700, background: 'transparent' }}>Shares</TableCell>
                <TableCell sx={{ color: '#bdbddd', fontWeight: 700, background: 'transparent' }}>Price</TableCell>
                <TableCell sx={{ color: '#bdbddd', fontWeight: 700, background: 'transparent' }}>Value</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(breakdown).length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} align="center" sx={{ color: '#bdbddd' }}>
                    No holdings found.
                  </TableCell>
                </TableRow>
              )}
              {Object.entries(breakdown).map(([symbol, info]: any) => (
                <TableRow key={symbol}>
                  <TableCell sx={{ color: '#fff' }}>{symbol}</TableCell>
                  <TableCell sx={{ color: '#fff' }}>{info.shares}</TableCell>
                  <TableCell sx={{ color: '#fff' }}>${info.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</TableCell>
                  <TableCell sx={{ color: '#fff' }}>${info.value?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
} 