import { testConnection } from '../lib/db';

async function main() {
  try {
    console.log('Testing database connection...');
    const isConnected = await testConnection();
    if (isConnected) {
      console.log('✅ Database connection successful!');
    } else {
      console.log('❌ Database connection failed!');
    }
  } catch (error) {
    console.error('Error testing connection:', error);
  }
  process.exit();
}

main(); 