"""Gunicorn production configuration.

Usage:
    gunicorn --config gunicorn.conf.py wsgi:app
"""

import multiprocessing
import os

# ---------------------------------------------------------------------------
# Binding
# ---------------------------------------------------------------------------
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------
# Default calculated based on CPU count
# Formula: (2 * CPU cores) + 1
_cpu_count = multiprocessing.cpu_count()
_default_workers = min((2 * _cpu_count) + 1, 12)  # cap at 12

workers = int(os.environ.get("GUNICORN_WORKERS", _default_workers))
threads = int(os.environ.get("GUNICORN_THREADS", 2))
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "gthread")

# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 60))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", 5))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", 30))

# ---------------------------------------------------------------------------
# Worker lifecycle
# ---------------------------------------------------------------------------
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", 50))
worker_tmp_dir = "/dev/shm"  # use shared memory for better performance

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "-")   # "-" = stdout
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "-")     # "-" = stderr
access_log_format = (
    '{"time":"%(t)s","remote_addr":"%(h)s","method":"%(m)s",'
    '"path":"%(U)s","status":%(s)s,"bytes":%(b)s,"duration_ms":%(D)s}'
)

# ---------------------------------------------------------------------------
# Process naming
# ---------------------------------------------------------------------------
proc_name = "saladetriagem"

# ---------------------------------------------------------------------------
# Lifecycle hooks
# ---------------------------------------------------------------------------


def on_starting(server):  # noqa: ARG001
    server.log.info("Gunicorn starting — %d worker(s), %d thread(s) each", workers, threads)
    server.log.info("Expected capacity: ~%d concurrent users", workers * threads * 5)


def worker_exit(server, worker):  # noqa: ARG001
    server.log.info("Worker %d exited", worker.pid)