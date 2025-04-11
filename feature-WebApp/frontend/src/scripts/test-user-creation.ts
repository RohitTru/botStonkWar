const { createUser, getUserByUsername, getUserByEmail } = require('../lib/db');
const bcrypt = require('bcrypt');

async function testUserCreation() {
  try {
    // Test user details
    const testUser = {
      username: 'testuser',
      email: 'test@example.com',
      password: 'TestPassword123!'
    };

    console.log('Testing user creation...');
    
    // Hash the password
    const saltRounds = 10;
    const passwordHash = await bcrypt.hash(testUser.password, saltRounds);

    // Try to create the user
    console.log('Creating user...');
    const result = await createUser(testUser.username, testUser.email, passwordHash);
    console.log('User creation result:', result);

    // Verify we can fetch the user by username
    console.log('\nTrying to fetch user by username...');
    const userByUsername = await getUserByUsername(testUser.username);
    console.log('Found user by username:', userByUsername ? 'Yes' : 'No');

    // Verify we can fetch the user by email
    console.log('\nTrying to fetch user by email...');
    const userByEmail = await getUserByEmail(testUser.email);
    console.log('Found user by email:', userByEmail ? 'Yes' : 'No');

    console.log('\n✅ Test completed successfully!');
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    process.exit();
  }
}

testUserCreation(); 