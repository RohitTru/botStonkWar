'use client';

import { AppBar, Toolbar, Typography, Button, Tabs, Tab } from '@mui/material';
import { useRouter } from 'next/navigation';

const DASHBOARD_LINKS = [
  { name: 'Web Scraper Engine', url: 'https://feature-webscraperstockselector.emerginary.com/' },
  { name: 'Sentiment Analysis Engine', url: 'https://feature-sentimentanalysisengine.emerginary.com/' },
  { name: 'Trade Recommendation Engine', url: 'https://feature-tradelogistics.emerginary.com/' },
  { name: 'Brokerage Handler Engine', url: 'https://feature-stockbot.emerginary.com/' },
];

export default function AdminNavbar({ activeIndex, setActiveIndex }: { activeIndex: number, setActiveIndex: (i: number) => void }) {
  const router = useRouter();

  const handleLogout = () => {
    document.cookie = 'auth_token=; Max-Age=0; path=/;';
    router.push('/');
  };

  return (
    <AppBar position="static" color="default" elevation={2}>
      <Toolbar sx={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <Typography variant="h6" fontWeight={700} sx={{ minWidth: 250 }}>
          BotStonkWar Admin Dashboard
        </Typography>
        <Tabs
          value={activeIndex}
          onChange={(_, newIndex) => setActiveIndex(newIndex)}
          textColor="primary"
          indicatorColor="primary"
          sx={{ flexGrow: 1, mx: 4, minWidth: 300 }}
          variant="scrollable"
          scrollButtons="auto"
        >
          {DASHBOARD_LINKS.map((link) => (
            <Tab key={link.name} label={link.name} />
          ))}
        </Tabs>
        <Button color="inherit" onClick={handleLogout} variant="outlined" sx={{ minWidth: 100 }}>
          Logout
        </Button>
      </Toolbar>
    </AppBar>
  );
} 