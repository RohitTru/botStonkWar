import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { verifyToken } from '@/lib/auth';
import { getUserById, getSession } from '@/lib/db';

export async function GET() {
  try {
    console.log('GET /api/auth/me called');
    
    // Get the auth token from cookies
    const token = cookies().get('auth_token')?.value;
    console.log('Auth token from cookie:', token ? 'Present' : 'Missing');
    
    if (!token) {
      console.log('No auth token found');
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
    }

    // Verify the token
    console.log('Verifying token');
    const payload = verifyToken(token);
    if (!payload) {
      console.log('Invalid token');
      return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
    }
    console.log('Token verified, payload:', payload);

    // Check if session exists in database
    console.log('Checking session in database');
    const session = await getSession(token);
    if (!session) {
      console.log('No valid session found');
      return NextResponse.json({ error: 'Session expired' }, { status: 401 });
    }
    console.log('Valid session found');

    // Special case for admin user
    if (payload.userId === 0 && payload.role === 'admin') {
      console.log('Admin user detected');
      return NextResponse.json({
        user: {
          id: 0,
          username: 'admin',
          email: 'admin@system',
          role: 'admin'
        }
      });
    }

    // Get user data for regular users
    console.log('Getting user data for regular user');
    const user = await getUserById(payload.userId);
    if (!user) {
      console.log('User not found in database');
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }
    console.log('User found:', user);

    return NextResponse.json({
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: 'user'
      }
    });
  } catch (error) {
    console.error('Error in /api/auth/me:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 