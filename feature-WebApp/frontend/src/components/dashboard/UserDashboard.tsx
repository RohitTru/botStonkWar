'use client';

import { Box, Typography, Paper, Card, CardContent } from '@mui/material';

export default function UserDashboard({ user }: { user: any }) {
  return (
    <Box sx={{ p: 3, minHeight: '100vh', background: '#181828' }}>
      <Card sx={{
        maxWidth: 300,
        mx: 'auto',
        mb: 3,
        background: 'linear-gradient(90deg, #7c5fff 0%, #6c47ff 100%)',
        boxShadow: 'none',
        borderRadius: 3,
        color: '#fff',
        border: '1px solid #7c5fff',
        position: 'relative',
        top: 24,
        zIndex: 2
      }}>
        <CardContent sx={{ textAlign: 'center', p: 2 }}>
          <Typography variant="subtitle2" sx={{ color: '#e0d7ff', letterSpacing: 1 }} gutterBottom>
            Account Balance
          </Typography>
          <Typography variant="h5" fontWeight={700} sx={{ color: '#fff' }}>
            ${user?.balance?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </Typography>
        </CardContent>
      </Card>
      <Paper sx={{
        p: 4,
        textAlign: 'center',
        background: '#23233a',
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