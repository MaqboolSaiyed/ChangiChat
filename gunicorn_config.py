import multiprocessing
import os

# Server socket
# Use the PORT environment variable provided by Render
port = os.environ.get("PORT", 8000)
bind = f"0.0.0.0:{port}"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Timeout
timeout = 120
keepalive = 5