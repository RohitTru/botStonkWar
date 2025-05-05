import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { verifyToken, JWTPayload } from '@/lib/auth';

export async function GET() {
  try {
    const token = cookies().get('auth_token')?.value;

    if (!token) {
      return NextResponse.json(
        { error: 'Not authenticated' },
        { status: 401 }
      );
    }

    const decoded = verifyToken(token);
    if (!decoded) {
      return NextResponse.json(
        { error: 'Invalid token' },
        { status: 401 }
      );
    }

    // Special case for admin
    if (decoded.username === 'admin') {
      return NextResponse.json({
        id: 0,
        username: 'admin',
        email: 'admin@system',
        role: 'admin'
      });
    }

    // Regular user: fetch from backend
    const response = await fetch(`${process.env.BACKEND_URL}/api/users/${decoded.userId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user data');
    }

    const userData = await response.json();
    // Always add role: 'user' for normal users
    return NextResponse.json({ ...userData, role: 'user' });
  } catch (error: any) {
    console.error('Error fetching user data:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to fetch user data' },
      { status: 500 }
    );
  }
} 