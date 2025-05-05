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
import { usePathname } from 'next/navigation';

export default function ExternalNavbar() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const pathname = usePathname();

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
          {pathname !== '/login' && (
            <Button
              component={Link}
              href="/login"
              color="inherit"
              size={isMobile ? 'small' : 'medium'}
            >
              Login
            </Button>
          )}
          {pathname !== '/signup' && (
            <Button
              component={Link}
              href="/signup"
              variant="contained"
              size={isMobile ? 'small' : 'medium'}
            >
              Sign Up
            </Button>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
} 