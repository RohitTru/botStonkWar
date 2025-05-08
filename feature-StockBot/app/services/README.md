# Services

This folder contains service classes and logic for interacting with external APIs, business logic, and background tasks.

- `alpaca_service.py`: Handles Alpaca API integration for trade execution and price fetching.
- `trade_service.py`: Core trade logic, notifications, and execution workflows.
- `position_service.py`: User position management and calculations.
- `cache_service.py`: In-memory or Redis caching for rate-limited data (e.g., live prices).

Add new services here as needed for additional business logic or integrations. 