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
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function Navbar() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Fetch user info to determine if logged in
  const fetchUser = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/auth/me');
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const handleLogout = async () => {
    document.cookie = 'auth_token=; Max-Age=0; path=/;';
    setUser(null);
    router.push('/');
    setTimeout(fetchUser, 100); // Re-fetch user state after logout
  };

  // Optionally, you can add a loading spinner here
  if (loading) return null;

  return (
    <AppBar position="sticky" color="default" elevation={1}>
      <Toolbar>
        <Typography
          variant="h6"
          component={Link}
          href="/"
          sx={{
            textDecoration: 'none',
            color: 'inherit',
            flexGrow: 1,
          }}
        >
          BotStonkWar
        </Typography>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {!user && pathname !== '/login' && (
            <Button
              component={Link}
              href="/login"
              color="inherit"
              size={isMobile ? 'small' : 'medium'}
            >
              Login
            </Button>
          )}
          {!user && pathname !== '/signup' && (
            <Button
              component={Link}
              href="/signup"
              variant="contained"
              size={isMobile ? 'small' : 'medium'}
            >
              Sign Up
            </Button>
          )}
          {user && (
            <Button
              color="inherit"
              onClick={handleLogout}
              size={isMobile ? 'small' : 'medium'}
            >
              Logout
            </Button>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
} 