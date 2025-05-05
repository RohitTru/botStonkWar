'use client';

import { Container, Paper, Box } from '@mui/material';
import { useAdminTab } from '@/components/AdminTabContext';

const DASHBOARD_LINKS = [
  { name: 'Web Scraper Engine', url: 'https://feature-webscraperstockselector.emerginary.com/' },
  { name: 'Sentiment Analysis Engine', url: 'https://feature-sentimentanalysisengine.emerginary.com/' },
  { name: 'Trade Recommendation Engine', url: 'https://feature-tradelogistics.emerginary.com/' },
  { name: 'Brokerage Handler Engine', url: 'https://feature-stockbot.emerginary.com/' },
];

export default function AdminDashboard() {
  const { activeIndex } = useAdminTab();
  const activeDashboard = DASHBOARD_LINKS[activeIndex];

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Container maxWidth={false} sx={{ flexGrow: 1, p: 2 }}>
        <Paper
          sx={{
            height: 'calc(100vh - 100px)',
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