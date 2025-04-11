import { createPool, RowDataPacket, ResultSetHeader, Pool } from 'mysql2/promise';

// Define interfaces for our database entities
interface User extends RowDataPacket {
  id: number;
  username: string;
  email: string;
  password_hash: string;
  created_at: Date;
  updated_at: Date;
}

interface Session extends RowDataPacket {
  id: string;
  user_id: number;
  expires_at: Date;
  created_at: Date;
}

// Database connection configuration
const dbConfig = {
  host: process.env.DB_HOST || '127.0.0.1',
  user: process.env.DB_USER || 'botstonkwar_user',
  password: process.env.DB_PASSWORD || 'botstonkwar_password',
  database: process.env.DB_NAME || 'botstonkwar-db',
  port: 3306
};

// Create a connection pool
const pool: Pool = createPool(dbConfig);

// Test the database connection
export async function testConnection(): Promise<boolean> {
  try {
    const connection = await pool.getConnection();
    await connection.ping();
    connection.release();
    return true;
  } catch (error) {
    console.error('Database connection error:', error);
    return false;
  }
}

export async function getConnection() {
  return pool.getConnection();
}

// User-related database functions
export async function createUser(username: string, email: string, passwordHash: string): Promise<ResultSetHeader> {
  try {
    const [result] = await pool.execute<ResultSetHeader>(
      'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
      [username, email, passwordHash]
    );
    return result;
  } catch (error) {
    console.error('Error creating user:', error);
    throw error;
  }
}

export async function getUserByUsername(username: string): Promise<User | undefined> {
  try {
    const [rows] = await pool.execute<User[]>(
      'SELECT * FROM users WHERE username = ?',
      [username]
    );
    return rows[0];
  } catch (error) {
    console.error('Error getting user:', error);
    throw error;
  }
}

export async function getUserByEmail(email: string): Promise<User | undefined> {
  try {
    const [rows] = await pool.execute<User[]>(
      'SELECT * FROM users WHERE email = ?',
      [email]
    );
    return rows[0];
  } catch (error) {
    console.error('Error getting user:', error);
    throw error;
  }
}

// Session-related database functions
export async function createSession(userId: number, sessionId: string, expiresAt: Date): Promise<ResultSetHeader> {
  try {
    const [result] = await pool.execute<ResultSetHeader>(
      'INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)',
      [sessionId, userId, expiresAt]
    );
    return result;
  } catch (error) {
    console.error('Error creating session:', error);
    throw error;
  }
}

export async function getSession(sessionId: string): Promise<Session | undefined> {
  try {
    const [rows] = await pool.execute<Session[]>(
      'SELECT * FROM sessions WHERE id = ? AND expires_at > NOW()',
      [sessionId]
    );
    return rows[0];
  } catch (error) {
    console.error('Error getting session:', error);
    throw error;
  }
}

export async function deleteSession(sessionId: string): Promise<ResultSetHeader> {
  try {
    const [result] = await pool.execute<ResultSetHeader>(
      'DELETE FROM sessions WHERE id = ?',
      [sessionId]
    );
    return result;
  } catch (error) {
    console.error('Error deleting session:', error);
    throw error;
  }
}

export default pool; 