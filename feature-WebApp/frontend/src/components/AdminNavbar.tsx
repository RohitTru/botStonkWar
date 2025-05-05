'use client';

import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { useRouter } from 'next/navigation';

export default function AdminNavbar() {
  const router = useRouter();

  const handleLogout = () => {
    document.cookie = 'auth_token=; Max-Age=0; path=/;';
    router.push('/');
  };

  return (
    <AppBar position="static" color="default" elevation={2}>
      <Toolbar sx={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center' }}>
          <Typography
            variant="h5"
            fontWeight={700}
            sx={{ letterSpacing: 2, color: 'primary.main', textAlign: 'center' }}
          >
            BotStonkWar Admin Dashboard
          </Typography>
        </Box>
        <Button color="inherit" onClick={handleLogout} variant="outlined" sx={{ minWidth: 100 }}>
          Logout
        </Button>
      </Toolbar>
    </AppBar>
  );
} 