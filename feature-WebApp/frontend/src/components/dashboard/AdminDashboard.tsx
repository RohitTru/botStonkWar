'use client';

import { useRouter } from 'next/navigation';
import { Box, Button, Container, Paper } from '@mui/material';
import { useState } from 'react';

const DASHBOARD_LINKS = [
  {
    name: 'Web Scraper Engine',
    url: 'https://feature-webscraperstockselector.emerginary.com/',
  },
  {
    name: 'Sentiment Analysis Engine',
    url: 'https://feature-sentimentanalysisengine.emerginary.com/',
  },
  {
    name: 'Trade Recommendation Engine',
    url: 'https://feature-tradelogistics.emerginary.com/',
  },
  {
    name: 'Brokerage Handler Engine',
    url: 'https://feature-stockbot.emerginary.com/',
  },
];

export default function AdminDashboard() {
  const [activeDashboard, setActiveDashboard] = useState(DASHBOARD_LINKS[0]);
  const router = useRouter();

  const handleLogout = () => {
    document.cookie = 'auth_token=; Max-Age=0; path=/;';
    router.push('/');
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 2 }}>
        <Button color="inherit" onClick={handleLogout} variant="outlined">
          Logout
        </Button>
      </Box>
      <Container maxWidth={false} sx={{ flexGrow: 1, p: 2 }}>
        <Paper
          sx={{
            height: 'calc(100vh - 120px)',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <iframe
            src={activeDashboard.url}
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
            }}
            title={activeDashboard.name}
          />
        </Paper>
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2, gap: 2 }}>
          {DASHBOARD_LINKS.map((link) => (
            <Button
              key={link.name}
              variant={activeDashboard.name === link.name ? 'contained' : 'outlined'}
              onClick={() => setActiveDashboard(link)}
            >
              {link.name}
            </Button>
          ))}
        </Box>
      </Container>
    </Box>
  );
} 