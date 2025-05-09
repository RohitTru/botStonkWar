import { useEffect, useState } from 'react';
import { Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, CircularProgress } from '@mui/material';

interface User {
  id: number;
  username: string;
  balance: number;
}

export default function LeaderboardPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await fetch('/api/users');
        if (!res.ok) throw new Error('Failed to fetch users');
        const data = await res.json();
        setUsers(data.sort((a: User, b: User) => b.balance - a.balance));
      } catch (e: any) {
        setError(e.message || 'Error fetching users');
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" sx={{ background: '#18191A' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" sx={{ background: '#18191A' }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

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
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user, idx) => (
              <TableRow key={user.id}>
                <TableCell sx={{ color: '#fff' }}>{idx + 1}</TableCell>
                <TableCell sx={{ color: '#fff' }}>{user.username}</TableCell>
                <TableCell sx={{ color: '#fff' }}>${user.balance?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
} 