import * as bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { createUser, getUserByUsername, getUserByEmail, createSession, deleteSession } from './db';

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const SALT_ROUNDS = 10;

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

export async function comparePasswords(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export async function registerUser(username: string, email: string, password: string) {
  try {
    // Check if username or email already exists
    const existingUsername = await getUserByUsername(username);
    if (existingUsername) {
      throw new Error('Username already exists');
    }

    const existingEmail = await getUserByEmail(email);
    if (existingEmail) {
      throw new Error('Email already exists');
    }

    // Hash password and create user
    const passwordHash = await hashPassword(password);
    const result = await createUser(username, email, passwordHash);
    return result;
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
}

export async function loginUser(username: string, password: string) {
  try {
    // Get user from database
    const user = await getUserByUsername(username);
    if (!user) {
      throw new Error('Invalid username or password');
    }

    // Verify password
    const isValid = await comparePasswords(password, user.password_hash);
    if (!isValid) {
      throw new Error('Invalid username or password');
    }

    // Create session token
    const token = jwt.sign(
      { userId: user.id, username: user.username },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    // Create session in database
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + 1); // 24 hours from now
    await createSession(user.id, token, expiresAt);

    return {
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        balance: user.balance,
      },
    };
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

export async function logoutUser(token: string) {
  try {
    await deleteSession(token);
    return true;
  } catch (error) {
    console.error('Logout error:', error);
    throw error;
  }
}

export function verifyToken(token: string) {
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (error) {
    return null;
  }
} 