'use client';

import { Container, Paper, Box, Button } from '@mui/material';
import { useState } from 'react';

const DASHBOARD_LINKS = [
  { name: 'Web Scraper Engine', url: 'https://feature-webscraperstockselector.emerginary.com/' },
  { name: 'Sentiment Analysis Engine', url: 'https://feature-sentimentanalysisengine.emerginary.com/' },
  { name: 'Trade Recommendation Engine', url: 'https://feature-tradelogistics.emerginary.com/' },
  { name: 'Brokerage Handler Engine', url: 'https://feature-stockbot.emerginary.com/' },
];

export default function AdminDashboard() {
  const [activeIndex, setActiveIndex] = useState(0);
  const activeDashboard = DASHBOARD_LINKS[activeIndex];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mt: 3, mb: 2, gap: 2 }}>
        {DASHBOARD_LINKS.map((link, idx) => (
          <Button
            key={link.name}
            variant={activeIndex === idx ? 'contained' : 'outlined'}
            color={activeIndex === idx ? 'primary' : 'inherit'}
            onClick={() => setActiveIndex(idx)}
            sx={{
              fontWeight: 600,
              fontSize: '1rem',
              px: 3,
              py: 1.5,
              borderRadius: 3,
              boxShadow: activeIndex === idx ? 2 : 0,
              transition: 'all 0.2s',
              letterSpacing: 1,
            }}
          >
            {link.name}
          </Button>
        ))}
      </Box>
      <Container maxWidth={false} sx={{ flexGrow: 1, p: 2 }}>
        <Paper
          sx={{
            height: 'calc(100vh - 140px)',
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
      </Container>
    </Box>
  );
} 