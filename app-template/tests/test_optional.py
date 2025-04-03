"""
Optional Tests
============

These tests are nice-to-have and won't block development or merging.
They help improve code quality, performance, and user experience.

When to Use Optional Tests:
------------------------
1. After mandatory and recommended tests pass
2. When optimizing performance
3. When improving user experience
4. When testing advanced features

All examples are commented out by default - uncomment them as you're ready to optimize.

Testing Concepts Covered:
----------------------
1. Performance testing
2. Load testing
3. User experience
4. Advanced error scenarios
5. Documentation verification
"""

import pytest
import time
from datetime import datetime

"""
# Example 1: Performance Test
# -------------------------
# When to uncomment: When you want to optimize response times
# What to modify: The performance thresholds for your feature

def test_trade_performance():
    '''
    Purpose: Ensure trading operations are fast enough
    What it does:
    1. Measures operation time
    2. Compares against threshold
    3. Reports detailed timing
    
    This helps identify slow operations
    '''
    # Performance thresholds (in seconds)
    ACCEPTABLE_TIME = 0.1
    OPTIMAL_TIME = 0.05
    
    # Start timing
    start_time = time.time()
    
    # Perform operation (example: create trade)
    trade_data = {
        "symbol": "AAPL",
        "amount": 100,
        "type": "BUY",
        "price": 150.50
    }
    
    # Your trade creation code here
    # create_trade(trade_data)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Performance assertions
    if execution_time > ACCEPTABLE_TIME:
        print(f"⚠️ Warning: Operation took {execution_time:.3f}s (Above acceptable {ACCEPTABLE_TIME}s)")
    elif execution_time > OPTIMAL_TIME:
        print(f"📊 Note: Operation took {execution_time:.3f}s (Above optimal {OPTIMAL_TIME}s)")
    else:
        print(f"✅ Operation completed in {execution_time:.3f}s")

# Example 2: Load Test
# ------------------
# When to uncomment: When testing system capacity
# What to modify: The load parameters for your feature

def test_concurrent_trades(client):
    '''
    Purpose: Test system behavior under load
    What it does:
    1. Simulates multiple concurrent trades
    2. Measures system response
    3. Checks for errors
    
    This helps understand system capacity
    '''
    import threading
    
    # Test parameters
    NUM_CONCURRENT_TRADES = 10
    TRADE_DELAY = 0.1  # seconds between trades
    
    # Track results
    successful_trades = 0
    failed_trades = 0
    
    def make_trade():
        nonlocal successful_trades, failed_trades
        try:
            response = client.post('/api/trades', json={
                "symbol": "AAPL",
                "amount": 100,
                "type": "BUY"
            })
            if response.status_code == 201:
                successful_trades += 1
            else:
                failed_trades += 1
        except Exception:
            failed_trades += 1
    
    # Create and run threads
    threads = []
    for _ in range(NUM_CONCURRENT_TRADES):
        t = threading.Thread(target=make_trade)
        threads.append(t)
        t.start()
        time.sleep(TRADE_DELAY)
    
    # Wait for all trades to complete
    for t in threads:
        t.join()
    
    # Report results
    print(f"Successful trades: {successful_trades}")
    print(f"Failed trades: {failed_trades}")
    print(f"Success rate: {(successful_trades/NUM_CONCURRENT_TRADES)*100:.1f}%")

# Example 3: User Experience Test
# ---------------------------
# When to uncomment: When improving user interaction
# What to modify: The UX requirements for your feature

def test_trade_feedback(client):
    '''
    Purpose: Verify quality of user feedback
    What it does:
    1. Tests error messages
    2. Verifies helpful responses
    3. Checks response format
    
    This helps improve user experience
    '''
    # Test cases with expected user feedback
    test_cases = [
        {
            "scenario": "Invalid symbol",
            "input": {"symbol": "INVALID", "amount": 100},
            "expected_message": "Invalid stock symbol. Please use valid NYSE symbols."
        },
        {
            "scenario": "Insufficient funds",
            "input": {"symbol": "AAPL", "amount": 1000000},
            "expected_message": "Insufficient funds for this trade."
        },
        {
            "scenario": "Market closed",
            "input": {"symbol": "AAPL", "amount": 100},
            "expected_message": "Market is currently closed. Trading hours are 9:30 AM - 4:00 PM EST."
        }
    ]
    
    for case in test_cases:
        response = client.post('/api/trades', json=case['input'])
        
        # Verify response has helpful message
        assert 'message' in response.json, f"Missing message in {case['scenario']}"
        assert len(response.json['message']) >= 10, f"Message too short in {case['scenario']}"
        assert response.json['message'] == case['expected_message'], f"Unclear message in {case['scenario']}"

# Example 4: Advanced Error Recovery
# ------------------------------
# When to uncomment: When implementing robust error handling
# What to modify: The recovery scenarios for your feature

def test_trade_recovery(client):
    '''
    Purpose: Test system recovery from errors
    What it does:
    1. Simulates various failures
    2. Checks recovery behavior
    3. Verifies system stability
    
    This helps ensure system reliability
    '''
    def simulate_error(client, error_type):
        if error_type == "network":
            # Simulate network timeout
            time.sleep(5)
            return client.post('/api/trades', json={})
        elif error_type == "database":
            # Simulate database connection error
            return client.post('/api/trades/force_db_error')
        elif error_type == "partial_failure":
            # Simulate partial system failure
            return client.post('/api/trades/partial_error')
    
    # Test recovery scenarios
    scenarios = ["network", "database", "partial_failure"]
    
    for scenario in scenarios:
        # Attempt operation that will fail
        response = simulate_error(client, scenario)
        
        # Verify system is still operational
        health_check = client.get('/health')
        assert health_check.status_code == 200, f"System unhealthy after {scenario} error"
        
        # Verify can still perform operations
        trade_response = client.post('/api/trades', json={
            "symbol": "AAPL",
            "amount": 100,
            "type": "BUY"
        })
        assert trade_response.status_code in [201, 400], f"System not accepting trades after {scenario} error"
"""

# Note for developers:
# ------------------
# How to use these examples:
# 1. Start with mandatory and recommended tests
# 2. Use these tests to optimize and improve
# 3. Don't worry if these tests fail initially
# 4. Focus on one improvement at a time
#
# Tips for optional tests:
# - Use print() for detailed feedback
# - Set realistic thresholds
# - Consider real-world conditions
# - Focus on user experience
# - Test recovery scenarios