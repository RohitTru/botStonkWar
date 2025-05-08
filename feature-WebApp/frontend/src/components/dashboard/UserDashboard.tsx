'use client';

import { Box, Typography, Paper, Card, CardContent } from '@mui/material';

export default function UserDashboard({ user }: { user: any }) {
  return (
    <Box sx={{ p: 3, minHeight: '100vh', background: '#18191A' }}>
      <Card sx={{
        width: 180,
        mx: 'auto',
        mb: 2,
        background: 'linear-gradient(90deg, #7c5fff 0%, #6c47ff 100%)',
        boxShadow: 'none',
        borderRadius: 2,
        color: '#fff',
        border: '1px solid #7c5fff',
        position: 'relative',
        top: 24,
        zIndex: 2,
        p: 0,
      }}>
        <CardContent sx={{ textAlign: 'center', p: 1.5 }}>
          <Typography variant="caption" sx={{ color: '#e0d7ff', letterSpacing: 1, fontSize: 13 }} gutterBottom>
            Liquidity
          </Typography>
          <Typography variant="h6" fontWeight={700} sx={{ color: '#fff', fontSize: 20 }}>
            ${user?.balance?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </Typography>
        </CardContent>
      </Card>
      <Paper sx={{
        p: 4,
        textAlign: 'center',
        background: '#232526',
        color: '#fff',
        borderRadius: 3,
        boxShadow: 'none',
        mt: 0
      }}>
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