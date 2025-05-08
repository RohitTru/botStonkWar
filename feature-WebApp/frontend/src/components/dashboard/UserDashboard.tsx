'use client';

import { Box, Typography, Paper, Card, CardContent } from '@mui/material';

export default function UserDashboard({ user }: { user: any }) {
  return (
    <Box sx={{ p: 3 }}>
      <Card sx={{ maxWidth: 400, mx: 'auto', mb: 3, background: 'linear-gradient(90deg, #e3ffe8 0%, #d9e7ff 100%)', boxShadow: 3 }}>
        <CardContent>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Account Balance
          </Typography>
          <Typography variant="h4" color="primary" fontWeight={700}>
            ${user?.balance?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </Typography>
        </CardContent>
      </Card>
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome to Your Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          This dashboard is currently under development. More features will be available soon.
        </Typography>
      </Paper>
    </Box>
  );
} 