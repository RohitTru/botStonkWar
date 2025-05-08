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

    // Regular user: fetch from database
    const user = await getUserByUsername(decoded.username);
    if (!user) {
      throw new Error('User not found');
    }

    // Always add role: 'user' for normal users
    return NextResponse.json({ 
      id: user.id,
      username: user.username,
      email: user.email,
      role: 'user'
    });
  } catch (error: any) {
    console.error('Error fetching user data:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to fetch user data' },
      { status: 500 }
    );
  }
} 