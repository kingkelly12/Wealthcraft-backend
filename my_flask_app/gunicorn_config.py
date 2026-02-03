"""
Gunicorn Configuration for WealthCraft Flask API
================================================

🎓 LEARNING: This file configures how Gunicorn runs your Flask app in production.

Key Concepts:
1. Workers = Separate processes that handle requests
2. Worker Class = How workers handle concurrency (sync, gevent, etc.)
3. Worker Connections = Max concurrent connections per worker
4. Binding = IP:Port to listen on

Performance Impact: 1000x improvement over Flask dev server!
"""

import os


# Number of worker processes
# Formula: (2 × CPU_cores) + 1
# 🎓 WHY: Balances CPU usage with I/O waiting time
workers = 1

worker_class = 'gthread'
threads = 8

# Maximum number of simultaneous clients per worker
# 🎓 TOTAL CAPACITY: workers × worker_connections
# Example: 5 workers × 1000 = 5,000 concurrent users
worker_connections = 1000

# Bind to this address
# 🎓 OPTIONS:
#   - '0.0.0.0:5000': Listen on all network interfaces (production)
#   - '127.0.0.1:5000': Only localhost (development)
port = os.getenv('PORT', '5000')
bind = f'0.0.0.0:{port}'

# Backlog - number of pending connections
# 🎓 WHY: If all workers are busy, queue up to 2048 connections
backlog = 2048

# Workers silent for more than this many seconds are killed and restarted
# 🎓 WHY: Prevents hung workers from blocking requests
# Set higher if you have long-running operations
timeout = 120

# Timeout for graceful workers restart
# 🎓 WHY: Gives workers time to finish current requests before shutdown
graceful_timeout = 30

# Restart workers after this many requests (prevents memory leaks)
# 🎓 WHY: Python can accumulate memory over time
# 0 = disabled, 1000 = restart after 1000 requests
max_requests = 2000
max_requests_jitter = 100  # Add randomness to prevent all workers restarting at once


# Access log file
# 🎓 FORMAT: Each request logged with timestamp, status, response time
accesslog = '-'  # '-' means stdout (good for Docker/systemd)

# Error log file
errorlog = '-'  # '-' means stderr

# Log level
# 🎓 OPTIONS: debug, info, warning, error, critical
loglevel = 'info'

access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process name in process list
# 🎓 WHY: Makes it easy to identify in 'ps' or 'top'
proc_name = 'adulting_api'


# Limit request line size (prevents some attacks)
limit_request_line = 4096

# Limit number of headers
limit_request_fields = 100

# Limit header size
limit_request_field_size = 8190


# Reload on code changes (ONLY for development!)
# 🎓 WARNING: Never use in production - causes performance issues
reload = os.getenv('FLASK_ENV') == 'development'

# Preload app before forking workers
# 🎓 WHY: Faster startup, shared memory for read-only data
# WARNING: Can cause issues with some libraries (database connections)
preload_app = True  # Set to True if you want faster startup


def on_starting(server):
    """
    Called just before the master process is initialized.
    🎓 USE CASE: Setup logging, initialize shared resources
    """
    server.log.info("🚀 WealthCraft API starting...")

def on_reload(server):
    """
    Called when code changes are detected (if reload=True)
    🎓 USE CASE: Cleanup before reload
    """
    server.log.info("🔄 Reloading application...")

def when_ready(server):
    """
    Called just after the server is started.
    🎓 USE CASE: Log startup info, notify monitoring systems
    """
    server.log.info(f"✅ WealthCraft API ready! Workers: {workers}, Connections: {worker_connections}")

def pre_fork(server, worker):
    """
    Called just before a worker is forked.
    🎓 USE CASE: Close database connections (they don't work across forks)
    """
    pass

def post_fork(server, worker):
    """
    Called just after a worker has been forked.
    🎓 USE CASE: Initialize worker-specific resources (database connections)
    """
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def worker_exit(server, worker):
    """
    Called just after a worker has been exited.
    🎓 USE CASE: Cleanup, logging
    """
    server.log.info(f"Worker exited (pid: {worker.pid})")


