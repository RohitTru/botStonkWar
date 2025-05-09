import { Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';

const mockLeaderboard = [
  { rank: 1, username: 'TraderJoe', equity: 15000, returns: 25.3 },
  { rank: 2, username: 'StonkQueen', equity: 14200, returns: 21.7 },
  { rank: 3, username: 'AlgoKing', equity: 13900, returns: 19.2 },
  { rank: 4, username: 'ValueVestor', equity: 13200, returns: 15.8 },
  { rank: 5, username: 'MomentumMike', equity: 12800, returns: 13.4 },
];

export default function LeaderboardPage() {
  return (
    <Box sx={{ p: 4, minHeight: '100vh', background: '#18191A', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Typography variant="h4" sx={{ color: '#fff', mb: 3 }}>Leaderboard</Typography>
      <TableContainer component={Paper} sx={{ maxWidth: 600, background: '#232526', borderRadius: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell sx={{ color: '#bdbddd', fontWeight: 700 }}>Rank</TableCell>
              <TableCell sx={{ color: '#bdbddd', fontWeight: 700 }}>Username</TableCell>
              <TableCell sx={{ color: '#b3e5fc', fontWeight: 700 }}>Equity</TableCell>
              <TableCell sx={{ color: '#43e97b', fontWeight: 700 }}>Returns (%)</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {mockLeaderboard.map(row => (
              <TableRow key={row.rank}>
                <TableCell sx={{ color: '#fff' }}>{row.rank}</TableCell>
                <TableCell sx={{ color: '#fff' }}>{row.username}</TableCell>
                <TableCell sx={{ color: '#fff' }}>${row.equity.toLocaleString()}</TableCell>
                <TableCell sx={{ color: '#fff' }}>{row.returns.toFixed(2)}%</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
} 