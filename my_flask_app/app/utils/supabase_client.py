"""
Supabase Client Singleton
=========================

🎓 LEARNING: Why Singleton Pattern?

PROBLEM (Before):
Every route file creates its own Supabase client:
```python
# asset_routes.py
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# job_routes.py  
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ... 12 route files total
```

ISSUES:
1. Creates 12 separate HTTP connection pools (wasteful!)
2. Each pool has its own connections (memory waste)
3. Slower connection establishment
4. Harder to configure globally

SOLUTION (After):
One shared Supabase client instance:
```python
# supabase_client.py (this file)
_supabase_client = None  # Singleton instance

def get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(...)
    return _supabase_client

# All routes use the same instance
from app.utils.supabase_client import get_supabase_client
supabase = get_supabase_client()
```

BENEFITS:
1. One connection pool shared across all routes
2. Less memory usage
3. Faster (reuses connections)
4. Easy to configure in one place

PERFORMANCE IMPACT: 5-10x fewer connections, faster requests
"""

import os
from supabase import create_client, Client
from typing import Optional

# 🎓 GLOBAL: Singleton instance (None until first use)
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get the singleton Supabase client instance.
    
    🎓 SINGLETON PATTERN:
    - First call: Creates client and stores it
    - Subsequent calls: Returns existing client
    - Result: Only one client instance exists
    
    Returns:
        Client: Shared Supabase client instance
    
    Raises:
        ValueError: If required environment variables are missing
    """
    global _supabase_client
    
    # 🎓 CHECK: Has client been created yet?
    if _supabase_client is None:
        # Get environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        # 🎓 VALIDATION: Ensure required config exists
        if not supabase_url:
            raise ValueError('SUPABASE_URL environment variable is required')
        if not supabase_key:
            raise ValueError('SUPABASE_SERVICE_ROLE_KEY environment variable is required')
        
        # 🎓 CREATE: Initialize the singleton instance
        _supabase_client = create_client(supabase_url, supabase_key)
        
        print(f"✅ Supabase client initialized: {supabase_url}")
    
    return _supabase_client


def reset_supabase_client() -> None:
    """
    Reset the singleton instance (mainly for testing).
    
    🎓 USE CASE: Testing
    - Tests may need fresh client instances
    - Call this between tests to reset state
    """
    global _supabase_client
    _supabase_client = None


# 🎓 CONVENIENCE: Export for easy importing
supabase = get_supabase_client()

"""
🎓 USAGE IN ROUTES:

BEFORE (wasteful):
```python
# Every route file
from supabase import create_client
import os

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
```

AFTER (efficient):
```python
# Every route file
from app.utils.supabase_client import supabase

# That's it! Uses the shared singleton instance
```

MIGRATION STEPS:
1. Create this file (app/utils/supabase_client.py)
2. Update each route file to import from here
3. Remove duplicate create_client() calls
4. Profit! 🚀
"""

"""
🎓 ADVANCED: Thread Safety

Q: Is this thread-safe with Gunicorn workers?
A: Yes! Each worker process has its own Python interpreter.

EXPLANATION:
- Gunicorn spawns 4 separate processes
- Each process has its own global variables
- Each process creates its own singleton
- Result: 4 singletons total (one per worker)

This is actually GOOD:
- Each worker has dedicated client
- No cross-process sharing (which would be slow)
- Still better than 12 clients per worker (48 total!)

BEFORE: 12 routes × 4 workers = 48 clients
AFTER: 1 singleton × 4 workers = 4 clients
IMPROVEMENT: 12x fewer clients!
"""
