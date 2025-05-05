'use client';

import { useState } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Paper,
} from '@mui/material';

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

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Admin Dashboard
          </Typography>
          {DASHBOARD_LINKS.map((link) => (
            <Button
              key={link.name}
              color="inherit"
              onClick={() => setActiveDashboard(link)}
              sx={{
                mx: 1,
                backgroundColor: activeDashboard.name === link.name ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
              }}
            >
              {link.name}
            </Button>
          ))}
        </Toolbar>
      </AppBar>
      
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
      </Container>
    </Box>
  );
} 