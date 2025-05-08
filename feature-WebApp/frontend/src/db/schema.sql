-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    balance DECIMAL(15, 2) DEFAULT 10000.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Trading strategies table
CREATE TABLE IF NOT EXISTS trading_strategies (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    creator_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users(id)
);

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    strategy_id INT,
    stock_symbol VARCHAR(10) NOT NULL,
    trade_type ENUM('BUY', 'SELL') NOT NULL,
    status ENUM('PROPOSED', 'APPROVED', 'REJECTED', 'EXECUTED', 'CLOSED') NOT NULL,
    entry_price DECIMAL(10, 2),
    exit_price DECIMAL(10, 2),
    quantity INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    closed_at TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies(id)
);

-- Trade votes table
CREATE TABLE IF NOT EXISTS trade_votes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    trade_id INT,
    user_id INT,
    vote ENUM('YES', 'NO') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trade_id) REFERENCES trades(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY unique_vote (trade_id, user_id)
);

-- User strategy subscriptions
CREATE TABLE IF NOT EXISTS strategy_subscriptions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    strategy_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies(id),
    UNIQUE KEY unique_subscription (user_id, strategy_id)
);

-- Sessions table for authentication
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id INT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Trade acceptances table
CREATE TABLE IF NOT EXISTS trade_acceptances (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    trade_id INT NOT NULL,
    allocation_amount DECIMAL(15, 2), -- For BUY
    allocation_shares INT,            -- For SELL
    status ENUM('ACCEPTED', 'DENIED') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (trade_id) REFERENCES trades(id)
);

-- User positions table
CREATE TABLE IF NOT EXISTS user_positions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    shares INT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
); 