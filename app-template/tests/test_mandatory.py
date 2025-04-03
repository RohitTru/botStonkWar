"""
Mandatory Tests
==============

These tests MUST pass before any code can be merged.
They focus on the most basic and critical functionality of your application.

For Beginners (How to Use This File):
-----------------------------------
1. Start with the test_health_check - it's enabled and works with the template
2. When adding new features, look at the example tests below
3. Uncomment and modify the example that matches what you're building
4. Each example shows a different type of test you might need

Testing Basics:
-------------
1. Each test function starts with 'test_'
2. Use descriptive names for your test functions
3. Each test should check one specific thing
4. Use assert statements to check if something is true
5. Add clear comments to explain what you're testing
"""

import pytest
from datetime import datetime

def test_health_check(client):
    """
    Health Check Test (ENABLED)
    ----------------
    Purpose: Verify that our API is up and running
    What it does: Makes a GET request to /health and checks the response
    Why it matters: If this fails, nothing else will work!
    
    Note: This is the only test enabled by default because it matches
    the endpoint that exists in the template app.py
    """
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

"""
# Example 1: API Endpoint Test
# ---------------------------
# When to uncomment: After adding a new API endpoint
# What to modify: The endpoint URL and expected response

def test_get_trade_endpoint(client):
    '''
    Purpose: Test if your new API endpoint works
    What it does: 
    1. Sends a request to your endpoint
    2. Checks if it gets the right response
    3. Validates the response format
    
    Example: Testing a GET /api/trade endpoint
    '''
    # Make a request to your endpoint
    response = client.get('/api/trade')
    
    # Check if request was successful
    assert response.status_code == 200, "API should return 200 OK"
    
    # Check if response has the right format
    assert 'trades' in response.json, "Response should have 'trades' field"
    assert isinstance(response.json['trades'], list), "Trades should be a list"

# Example 2: Data Validation Test
# -----------------------------
# When to uncomment: When adding data validation to your feature
# What to modify: The validation rules for your data

def test_trade_data_validation():
    '''
    Purpose: Ensure trade data is valid before processing
    What it does:
    1. Creates sample trade data
    2. Checks if all required fields are present
    3. Validates data types and values
    '''
    # Example trade data - modify for your feature
    trade = {
        "symbol": "AAPL",
        "amount": 100,
        "type": "BUY",
        "price": 150.50
    }
    
    # Required field checks
    required_fields = ["symbol", "amount", "type", "price"]
    for field in required_fields:
        assert field in trade, f"Trade must include {field}"
    
    # Data type checks
    assert isinstance(trade["symbol"], str), "Symbol must be a string"
    assert isinstance(trade["amount"], (int, float)), "Amount must be a number"
    assert isinstance(trade["price"], float), "Price must be a float"
    
    # Value range checks
    assert trade["amount"] > 0, "Amount must be positive"
    assert trade["price"] > 0, "Price must be positive"
    assert trade["type"] in ["BUY", "SELL"], "Type must be BUY or SELL"

# Example 3: Calculation Test
# -------------------------
# When to uncomment: When adding calculations to your feature
# What to modify: The calculation logic and expected results

def test_trade_calculations():
    '''
    Purpose: Verify trading calculations are correct
    What it does:
    1. Sets up test values
    2. Performs calculations
    3. Compares with expected results
    '''
    # Test data
    price = 150.50
    quantity = 10
    commission_rate = 0.01  # 1%
    
    # Calculate total cost
    subtotal = price * quantity
    commission = subtotal * commission_rate
    total = subtotal + commission
    
    # Verify calculations (rounded to 2 decimal places)
    assert round(subtotal, 2) == 1505.00, "Subtotal calculation incorrect"
    assert round(commission, 2) == 15.05, "Commission calculation incorrect"
    assert round(total, 2) == 1520.05, "Total calculation incorrect"

# Example 4: Error Handling Test
# ---------------------------
# When to uncomment: When adding error handling to your feature
# What to modify: The error conditions and expected responses

def test_trade_error_handling(client):
    '''
    Purpose: Ensure your feature handles errors properly
    What it does:
    1. Tests various error conditions
    2. Verifies proper error responses
    3. Checks error message format
    '''
    # Test invalid trade data
    invalid_trade = {
        "symbol": "",  # Empty symbol
        "amount": -100,  # Negative amount
        "type": "INVALID"  # Invalid type
    }
    
    # Make request with invalid data
    response = client.post('/api/trade', json=invalid_trade)
    
    # Check error response
    assert response.status_code == 400, "Should return 400 for invalid data"
    assert 'error' in response.json, "Should include error message"
    assert isinstance(response.json['error'], str), "Error should be string"
"""

# Note for developers:
# ------------------
# How to add your own test:
# 1. Look at the examples above and find one similar to what you need
# 2. Copy and uncomment the example
# 3. Modify it for your feature
# 4. Make sure to test all important aspects of your feature
#
# Remember:
# - Start simple: Test the most basic functionality first
# - Be specific: Each test should check one thing
# - Add comments: Help others understand your test
# - Use descriptive names: Make it clear what you're testing