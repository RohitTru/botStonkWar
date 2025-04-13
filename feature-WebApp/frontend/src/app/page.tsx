import { Container, Typography, Button, Box, Paper, Grid } from '@mui/material';
import Link from 'next/link';

export default function Home() {
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h2" component="h1" gutterBottom align="center">
          Welcome to BotStonkWar
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom align="center" color="text.secondary">
          Democratize Your Trading Strategy
        </Typography>
        
        <Grid container spacing={4} sx={{ mt: 4 }}>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                About Us
              </Typography>
              <Typography paragraph>
                BotStonkWar is a platform that combines AI-powered trading strategies with community voting to democratize trading decisions.
                Join our community of traders and investors to share strategies and grow together.
              </Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                How It Works
              </Typography>
              <Typography paragraph>
                1. Create an account and deposit funds
                2. Join or create trading strategies
                3. Vote on trades and share insights
                4. Watch your portfolio grow
              </Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Get Started
              </Typography>
              <Typography paragraph>
                Ready to join the trading revolution? Sign up now and start your journey
                with BotStonkWar.
              </Typography>
              <Button
                component={Link}
                href="/signup"
                variant="contained"
                sx={{ mt: 2 }}
              >
                Sign Up Now
              </Button>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
}
