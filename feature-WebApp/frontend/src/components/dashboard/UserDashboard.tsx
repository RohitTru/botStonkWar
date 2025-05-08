'use client';

import { Box, Typography, Paper, Card, CardContent } from '@mui/material';

export default function UserDashboard({ user }: { user: any }) {
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