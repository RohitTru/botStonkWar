'use client';

import { Container, Paper, Box, Button } from '@mui/material';
import { useState } from 'react';
import SystemMonitor from './SystemMonitor';

const DASHBOARD_LINKS = [
  { name: 'Web Scraper Engine', url: 'https://feature-webscraperstockselector.emerginary.com/' },
  { name: 'Sentiment Analysis Engine', url: 'https://feature-sentimentanalysisengine.emerginary.com/' },
  { name: 'Trade Recommendation Engine', url: 'https://feature-tradelogistics.emerginary.com/' },
  { name: 'Brokerage Handler Engine', url: 'https://feature-stockbot.emerginary.com/' },
  { name: 'System Monitor', url: null },
];

export default function AdminDashboard() {
  const [activeIndex, setActiveIndex] = useState(0);
  const activeDashboard = DASHBOARD_LINKS[activeIndex];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#f8f9fa' }}>
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mt: 3, mb: 2, gap: 1 }}>
        {DASHBOARD_LINKS.map((link, idx) => (
          <Button
            key={link.name}
            variant="outlined"
            color="inherit"
            onClick={() => setActiveIndex(idx)}
            sx={{
              fontWeight: 500,
              fontSize: '0.95rem',
              px: 2,
              py: 0.5,
              borderRadius: 2,
              borderColor: activeIndex === idx ? '#222' : '#ccc',
              backgroundColor: activeIndex === idx ? '#f5f5f5' : 'transparent',
              color: '#222',
              boxShadow: 'none',
              textTransform: 'none',
              letterSpacing: 0.5,
              transition: 'all 0.15s',
              '&:hover': {
                backgroundColor: '#ececec',
                borderColor: '#222',
              },
            }}
          >
            {link.name}
          </Button>
        ))}
      </Box>
      {activeDashboard.name === 'System Monitor' ? (
        <SystemMonitor />
      ) : (
        <Container maxWidth={false} sx={{ flexGrow: 1, p: 2 }}>
          <Paper
            sx={{
              height: 'calc(100vh - 140px)',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <iframe
              src={activeDashboard.url as string}
              style={{
                width: '100%',
                height: '100%',
                border: 'none',
              }}
              title={activeDashboard.name}
            />
          </Paper>
        </Container>
      )}
    </Box>
  );
} 