'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Typography, CircularProgress } from '@mui/material';
import AdminDashboard from '@/components/dashboard/AdminDashboard';
import UserDashboard from '@/components/dashboard/UserDashboard';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        console.log('Fetching user data...');
        const response = await fetch('/api/auth/me');
        console.log('Auth response status:', response.status);
        
        if (!response.ok) {
          console.log('Auth failed, redirecting to login');
          router.push('/login');
          return;
        }
        
        const data = await response.json();
        console.log('User data received:', data);
        
        if (!data.user || !data.user.role) {
          console.error('Invalid user data received:', data);
          setError('Invalid user data');
          return;
        }
        
        setUser(data.user);
      } catch (error) {
        console.error('Error fetching user data:', error);
        setError('Failed to fetch user data');
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [router]);

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
    <Box sx={{ minHeight: '100vh', width: '100vw', background: '#18191A' }}>
      {user?.role === 'admin' ? (
        <AdminDashboard />
      ) : (
        <UserDashboard user={user} />
      )}
    </Box>
  );
} 