'use client';

import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';

export default function InternalNavbar() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    document.cookie = 'auth_token=; Max-Age=0; path=/;';
    router.push('/');
  };

  return (
    <AppBar position="sticky" sx={{ background: '#181828', color: '#fff', boxShadow: 'none', borderBottom: '1px solid #23233a' }}>
      <Toolbar>
        <Typography
          variant="h6"
          component={Link}
          href="/dashboard"
          sx={{
            textDecoration: 'none',
            color: '#fff',
            flexGrow: 1,
            fontWeight: 700,
            letterSpacing: 1.5,
          }}
        >
          BotStonkWar
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            component={Link}
            href="/dashboard"
            sx={{
              color: pathname === '/dashboard' ? '#a385ff' : '#fff',
              fontWeight: pathname === '/dashboard' ? 700 : 400,
              background: pathname === '/dashboard' ? 'rgba(124,95,255,0.08)' : 'none',
              borderRadius: 2,
              px: 2,
              textTransform: 'none',
            }}
            size={isMobile ? 'small' : 'medium'}
          >
            Dashboard
          </Button>
          {/* Add more internal links here */}
          <Button
            sx={{ color: '#fff', border: '1px solid #7c5fff', borderRadius: 2, px: 2, ml: 1, textTransform: 'none' }}
            onClick={handleLogout}
            size={isMobile ? 'small' : 'medium'}
          >
            Logout
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
} 