# Test Structure Guide

## Overview
This directory contains three categories of tests, organized by their importance and requirement level:

1. **Mandatory Tests** (`test_mandatory.py`)
   - Must pass before any code can be merged
   - Focus on critical functionality
   - Only basic health check enabled by default
   - Example: API health, critical routes

2. **Recommended Tests** (`test_recommended.py`)
   - Should pass before code is merged
   - Important but not critical
   - All examples commented out by default
   - Example: Integration flows, error handling

3. **Optional Tests** (`test_optional.py`)
   - Nice-to-have tests
   - Not blocking for deployments
   - Focus on performance and edge cases
   - All examples commented out by default

## Quick Start

```bash
# Run only mandatory tests
python -m pytest tests/test_mandatory.py

# Run mandatory and recommended tests
python -m pytest tests/test_mandatory.py tests/test_recommended.py

# Run all tests including optional
python -m pytest tests/

# Run with coverage report
python -m pytest tests/ --cov=. --cov-report=term-missing
```

## Test Development Guide

### When Adding New Features

1. Start with Mandatory Tests:
   - Uncomment relevant tests in `test_mandatory.py`
   - Add your critical test cases
   - Ensure they pass

2. Add Recommended Tests:
   - Uncomment relevant tests in `test_recommended.py`
   - Add integration and error handling tests
   - Verify functionality

3. Consider Optional Tests:
   - Add performance tests if needed
   - Test edge cases
   - Monitor resource usage

### Best Practices

1. **Mandatory Tests**
   - Keep them minimal and fast
   - Focus on critical paths
   - Must always pass

2. **Recommended Tests**
   - Test complete workflows
   - Verify error handling
   - Check data consistency

3. **Optional Tests**
   - Use soft assertions
   - Include performance metrics
   - Test edge cases

### Example Usage

```python
# In test_mandatory.py
def test_critical_feature():
    # Test critical functionality
    assert critical_function() == expected_result

# In test_recommended.py
def test_workflow():
    # Test complete workflow
    result = perform_workflow()
    assert result.status == 'success'

# In test_optional.py
def test_performance():
    start_time = time.time()
    # Test performance
    duration = time.time() - start_time
    assert duration < threshold  # Soft assertion
```

## Directory Structure
```
tests/
├── README.md           # This guide
├── test_mandatory.py   # Critical tests that must pass
├── test_recommended.py # Important but not critical tests
└── test_optional.py    # Nice-to-have tests
```

## Test Categories in Detail

### Mandatory Tests
- Health checks
- Critical API endpoints
- Basic data validation
- Core business logic
- Essential security checks

### Recommended Tests
- Integration flows
- Error handling
- Authentication flows
- Data consistency
- Rate limiting

### Optional Tests
- Performance metrics
- Load testing
- Edge cases
- UI responsiveness
- Memory usage
- Documentation accuracy

## Contributing

1. **Adding New Tests**
   - Choose appropriate category
   - Follow existing patterns
   - Add clear documentation
   - Include both specific and general examples

2. **Modifying Tests**
   - Keep mandatory tests minimal
   - Comment out example code
   - Update documentation
   - Maintain test independence

3. **Test Documentation**
   - Clear purpose statement
   - Usage examples
   - When to use/modify
   - Expected outcomes

## Common Patterns

### Test Structure
```python
def test_something():
    '''
    Purpose: What this test verifies
    When to use: When to implement/modify
    How to modify: How to customize
    
    Example - Project Specific:
    - Specific use case
    - Expected behavior
    
    Example - General Use:
    - Generic use case
    - Common patterns
    '''
    # Test implementation
```

### Assertion Patterns
```python
# Mandatory test - strict
assert result == expected, "Critical failure"

# Recommended test - with context
assert response.status_code == 200, "API should return success"

# Optional test - soft assertion
if performance > threshold:
    print(f"Warning: Performance above threshold: {performance}")
``` # Test Structure Guide

## Overview
This directory contains three categories of tests, organized by their importance and requirement level:

1. **Mandatory Tests** (`test_mandatory.py`)
   - Must pass before any code can be merged
   - Focus on critical functionality
   - Only basic health check enabled by default
   - Example: API health, critical routes

2. **Recommended Tests** (`test_recommended.py`)
   - Should pass before code is merged
   - Important but not critical
   - All examples commented out by default
   - Example: Integration flows, error handling

3. **Optional Tests** (`test_optional.py`)
   - Nice-to-have tests
   - Not blocking for deployments
   - Focus on performance and edge cases
   - All examples commented out by default

## Quick Start

```bash
# Run only mandatory tests
python -m pytest tests/test_mandatory.py

# Run mandatory and recommended tests
python -m pytest tests/test_mandatory.py tests/test_recommended.py

# Run all tests including optional
python -m pytest tests/

# Run with coverage report
python -m pytest tests/ --cov=. --cov-report=term-missing
```

## Test Development Guide

### When Adding New Features

1. Start with Mandatory Tests:
   - Uncomment relevant tests in `test_mandatory.py`
   - Add your critical test cases
   - Ensure they pass

2. Add Recommended Tests:
   - Uncomment relevant tests in `test_recommended.py`
   - Add integration and error handling tests
   - Verify functionality

3. Consider Optional Tests:
   - Add performance tests if needed
   - Test edge cases
   - Monitor resource usage

### Best Practices

1. **Mandatory Tests**
   - Keep them minimal and fast
   - Focus on critical paths
   - Must always pass

2. **Recommended Tests**
   - Test complete workflows
   - Verify error handling
   - Check data consistency

3. **Optional Tests**
   - Use soft assertions
   - Include performance metrics
   - Test edge cases

### Example Usage

```python
# In test_mandatory.py
def test_critical_feature():
    # Test critical functionality
    assert critical_function() == expected_result

# In test_recommended.py
def test_workflow():
    # Test complete workflow
    result = perform_workflow()
    assert result.status == 'success'

# In test_optional.py
def test_performance():
    start_time = time.time()
    # Test performance
    duration = time.time() - start_time
    assert duration < threshold  # Soft assertion
```

## Directory Structure
```
tests/
├── README.md           # This guide
├── test_mandatory.py   # Critical tests that must pass
├── test_recommended.py # Important but not critical tests
└── test_optional.py    # Nice-to-have tests
```

## Test Categories in Detail

### Mandatory Tests
- Health checks
- Critical API endpoints
- Basic data validation
- Core business logic
- Essential security checks

### Recommended Tests
- Integration flows
- Error handling
- Authentication flows
- Data consistency
- Rate limiting

### Optional Tests
- Performance metrics
- Load testing
- Edge cases
- UI responsiveness
- Memory usage
- Documentation accuracy

## Contributing

1. **Adding New Tests**
   - Choose appropriate category
   - Follow existing patterns
   - Add clear documentation
   - Include both specific and general examples

2. **Modifying Tests**
   - Keep mandatory tests minimal
   - Comment out example code
   - Update documentation
   - Maintain test independence

3. **Test Documentation**
   - Clear purpose statement
   - Usage examples
   - When to use/modify
   - Expected outcomes

## Common Patterns

### Test Structure
```python
def test_something():
    '''
    Purpose: What this test verifies
    When to use: When to implement/modify
    How to modify: How to customize
    
    Example - Project Specific:
    - Specific use case
    - Expected behavior
    
    Example - General Use:
    - Generic use case
    - Common patterns
    '''
    # Test implementation
```

### Assertion Patterns
```python
# Mandatory test - strict
assert result == expected, "Critical failure"

# Recommended test - with context
assert response.status_code == 200, "API should return success"

# Optional test - soft assertion
if performance > threshold:
    print(f"Warning: Performance above threshold: {performance}")
``` 