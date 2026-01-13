import multiprocessing
import os

# =====================================================
# SERVER SOCKET
# =====================================================
# Render assigns a dynamic port; we must use the PORT env var.
# If PORT isn't found, it defaults to 10000 (Render's common default).
port = os.environ.get('PORT', '10000')
bind = f'0.0.0.0:{port}'

# =====================================================
# WORKER CONFIGURATION
# =====================================================
# Render's free tier has limited CPU. 
# It's safer to let Render's WEB_CONCURRENCY decide the worker count.
workers = int(os.environ.get('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))

worker_class = 'gevent'
worker_connections = 1000
backlog = 2048

# =====================================================
# WORKER LIFECYCLE
# =====================================================
timeout = 120
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 50

# =====================================================
# LOGGING
# =====================================================
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# =====================================================
# PROCESS NAMING
# =====================================================
proc_name = 'wealthcraft_api'

# =====================================================
# SECURITY
# =====================================================
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# =====================================================
# DEVELOPMENT vs PRODUCTION
# =====================================================
# Note: Render usually sets FLASK_ENV or NODE_ENV. 
# We'll default to False for safety.
reload = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
preload_app = False 

# =====================================================
# WORKER HOOKS
# =====================================================
def on_starting(server):
    server.log.info("🚀 WealthCraft API starting on Render...")

def when_ready(server):
    server.log.info(f"✅ WealthCraft API ready! Port: {port}, Workers: {workers}")

def post_fork(server, worker):
    server.log.info(f"Worker spawned (pid: {worker.pid})")