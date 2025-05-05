'use client';

import { Container, Paper, Box } from '@mui/material';
import { useAdminTab, DASHBOARD_LINKS } from '@/components/AdminTabContext';

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