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
    <AppBar position="sticky" color="default" elevation={1}>
      <Toolbar>
        <Typography
          variant="h6"
          component={Link}
          href="/dashboard"
          sx={{
            textDecoration: 'none',
            color: 'inherit',
            flexGrow: 1,
          }}
        >
          BotStonkWar
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {/* Example internal navigation links, add more as needed */}
          <Button
            component={Link}
            href="/dashboard"
            color={pathname === '/dashboard' ? 'primary' : 'inherit'}
            size={isMobile ? 'small' : 'medium'}
          >
            Dashboard
          </Button>
          {/* Add more internal links here */}
          <Button
            color="inherit"
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