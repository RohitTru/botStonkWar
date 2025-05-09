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

export default function InternalNavbar({ user }: { user?: any }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = () => {
    document.cookie = 'auth_token=; Max-Age=0; path=/;';
    router.push('/');
  };

  return (
    <AppBar position="sticky" sx={{ background: '#20203a', color: '#fff', boxShadow: 'none', borderBottom: '1px solid #23233a' }}>
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
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Button
            component={Link}
            href="/dashboard"
            sx={{
              color: '#fff',
              fontWeight: pathname === '/dashboard' ? 700 : 400,
              background: pathname === '/dashboard' ? 'linear-gradient(90deg, #7c5fff 0%, #6c47ff 100%)' : 'none',
              borderRadius: 2,
              px: 2,
              textTransform: 'none',
              boxShadow: pathname === '/dashboard' ? '0 2px 8px 0 rgba(124,95,255,0.10)' : 'none',
              transition: 'background 0.2s',
            }}
            size={isMobile ? 'small' : 'medium'}
          >
            Trades
          </Button>
          <Button
            component={Link}
            href="/leaderboard"
            sx={{
              color: '#fff',
              fontWeight: pathname === '/leaderboard' ? 700 : 400,
              background: pathname === '/leaderboard' ? 'linear-gradient(90deg, #7c5fff 0%, #6c47ff 100%)' : 'none',
              borderRadius: 2,
              px: 2,
              textTransform: 'none',
              boxShadow: pathname === '/leaderboard' ? '0 2px 8px 0 rgba(124,95,255,0.10)' : 'none',
              transition: 'background 0.2s',
            }}
            size={isMobile ? 'small' : 'medium'}
          >
            Leaderboard
          </Button>
          <Button
            component={Link}
            href="/portfolio"
            sx={{
              color: '#fff',
              fontWeight: pathname === '/portfolio' ? 700 : 400,
              background: pathname === '/portfolio' ? 'linear-gradient(90deg, #7c5fff 0%, #6c47ff 100%)' : 'none',
              borderRadius: 2,
              px: 2,
              textTransform: 'none',
              boxShadow: pathname === '/portfolio' ? '0 2px 8px 0 rgba(124,95,255,0.10)' : 'none',
              transition: 'background 0.2s',
            }}
            size={isMobile ? 'small' : 'medium'}
          >
            Portfolio
          </Button>
          <Button
            sx={{ color: '#fff', border: '1px solid #7c5fff', borderRadius: 2, px: 2, ml: 1, textTransform: 'none', background: 'rgba(124,95,255,0.08)' }}
            onClick={handleLogout}
            size={isMobile ? 'small' : 'medium'}
          >
            Logout
          </Button>
          {user?.username && (
            <Typography sx={{ color: '#bdbddd', fontSize: 14, ml: 2 }}>
              Logged in as <b>{user.username}</b>
            </Typography>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
} 