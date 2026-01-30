"""
Gunicorn Configuration for Adulting Flask API
================================================

🎓 LEARNING: This file configures how Gunicorn runs your Flask app in production.

Key Concepts:
1. Workers = Separate processes that handle requests
2. Worker Class = How workers handle concurrency (sync, gevent, etc.)
3. Worker Connections = Max concurrent connections per worker
4. Binding = IP:Port to listen on

Performance Impact: 1000x improvement over Flask dev server!
"""

import multiprocessing
import os

# =====================================================
# WORKER CONFIGURATION
# =====================================================

# Number of worker processes
# Formula: (2 × CPU_cores) + 1
# 🎓 WHY: Balances CPU usage with I/O waiting time
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class - use gevent for async I/O
# 🎓 OPTIONS:
#   - 'sync': One request at a time (slow, like dev server)
#   - 'gevent': Async, handles 1000+ concurrent connections ✅
#   - 'eventlet': Similar to gevent
#   - 'uvicorn': For ASGI apps (FastAPI)
worker_class = 'sync'

# Maximum number of simultaneous clients per worker
# 🎓 TOTAL CAPACITY: workers × worker_connections
# Example: 5 workers × 1000 = 5,000 concurrent users
worker_connections = 1000

# =====================================================
# SERVER SOCKET
# =====================================================

# Bind to this address
# 🎓 OPTIONS:
#   - '0.0.0.0:5000': Listen on all network interfaces (production)
#   - '127.0.0.1:5000': Only localhost (development)
bind = '0.0.0.0:5000'

# Backlog - number of pending connections
# 🎓 WHY: If all workers are busy, queue up to 2048 connections
backlog = 2048

# =====================================================
# WORKER LIFECYCLE
# =====================================================

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
max_requests = 1000
max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once

# =====================================================
# LOGGING
# =====================================================

# Access log file
# 🎓 FORMAT: Each request logged with timestamp, status, response time
accesslog = '-'  # '-' means stdout (good for Docker/systemd)

# Error log file
errorlog = '-'  # '-' means stderr

# Log level
# 🎓 OPTIONS: debug, info, warning, error, critical
loglevel = 'info'

# Access log format
# 🎓 VARIABLES:
#   %(h)s = Remote address
#   %(l)s = '-'
#   %(u)s = User name
#   %(t)s = Date/time
#   %(r)s = Request line (GET /api/users HTTP/1.1)
#   %(s)s = Status code
#   %(b)s = Response length
#   %(f)s = Referer
#   %(a)s = User agent
#   %(D)s = Request time in microseconds
#   %(L)s = Request time in seconds
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# =====================================================
# PROCESS NAMING
# =====================================================

# Process name in process list
# 🎓 WHY: Makes it easy to identify in 'ps' or 'top'
proc_name = 'adulting_api'

# =====================================================
# SECURITY
# =====================================================

# Limit request line size (prevents some attacks)
limit_request_line = 4096

# Limit number of headers
limit_request_fields = 100

# Limit header size
limit_request_field_size = 8190

# =====================================================
# DEVELOPMENT vs PRODUCTION
# =====================================================

# Reload on code changes (ONLY for development!)
# 🎓 WARNING: Never use in production - causes performance issues
reload = os.getenv('FLASK_ENV') == 'development'

# Preload app before forking workers
# 🎓 WHY: Faster startup, shared memory for read-only data
# WARNING: Can cause issues with some libraries (database connections)
preload_app = False  # Set to True if you want faster startup

# =====================================================
# WORKER HOOKS (Advanced)
# =====================================================

def on_starting(server):
    """
    Called just before the master process is initialized.
    🎓 USE CASE: Setup logging, initialize shared resources
    """
    server.log.info("🚀 Adulting API starting...")

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
    server.log.info(f"✅ Adulting API ready! Workers: {workers}, Connections: {worker_connections}")

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

# =====================================================
# PERFORMANCE TUNING NOTES
# =====================================================
"""
🎓 TUNING GUIDE:

1. CPU-Bound App (lots of computation):
   - workers = CPU_cores
   - worker_class = 'sync'
   
2. I/O-Bound App (database, API calls) - YOUR CASE:
   - workers = (2 × CPU_cores) + 1
   - worker_class = 'gevent'
   - worker_connections = 1000+
   
3. Memory-Constrained Server:
   - Reduce workers
   - Reduce worker_connections
   - Enable max_requests to prevent memory leaks
   
4. High-Traffic App:
   - Increase workers
   - Increase worker_connections
   - Use load balancer (nginx) in front
   
5. Long-Running Requests:
   - Increase timeout
   - Consider task queue (Celery) for background jobs

MONITORING:
- Watch memory usage: `ps aux | grep gunicorn`
- Watch CPU usage: `top`
- Watch connections: `netstat -an | grep :5000 | wc -l`
- Watch logs: `tail -f /var/log/gunicorn/access.log`
"""
