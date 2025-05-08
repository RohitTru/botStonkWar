import { NextResponse } from 'next/server';
import { loginUser } from '@/lib/auth';
import { cookies } from 'next/headers';

export async function POST(request: Request) {
  try {
    console.log('Login API route hit');
    const { username, password } = await request.json();
    console.log('Login attempt for username:', username);

    // Validate input
    if (!username || !password) {
      console.log('Missing required fields');
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Login user
    console.log('Attempting to login user');
    const { token, user } = await loginUser(username, password);
    console.log('Login successful, user:', user);

    // Set cookie
    console.log('Setting auth cookie');
    cookies().set('auth_token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 60 * 60 * 24, // 24 hours
      path: '/',
    });

    console.log('Returning successful response');
    return NextResponse.json({ user }, { status: 200 });
  } catch (error: any) {
    console.error('Login error in API route:', error);
    return NextResponse.json(
      { error: error.message || 'Login failed' },
      { status: 401 }
    );
  }
} 