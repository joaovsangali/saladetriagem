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
# Formula: (2 × CPU cores) + 1  —  good for I/O-bound Flask apps
_default_workers = (2 * multiprocessing.cpu_count()) + 1
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
    server.log.info("Gunicorn starting — %d worker(s)", workers)


def worker_exit(server, worker):  # noqa: ARG001
    server.log.info("Worker %d exited", worker.pid)
