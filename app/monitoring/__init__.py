"""Prometheus metrics integration.

When ``prometheus-flask-exporter`` is installed, this module registers a
``/metrics`` endpoint that exposes standard HTTP metrics.

If the package is not installed, this module is a no-op (graceful fallback).
"""

import logging

logger = logging.getLogger(__name__)

_metrics = None


def init_metrics(app):
    """Register Prometheus metrics on *app* if the package is available."""
    global _metrics
    try:
        from prometheus_flask_exporter import PrometheusMetrics

        _metrics = PrometheusMetrics(app, group_by="endpoint")
        _metrics.info("app_info", "Sala de Triagem", version="1.0")
        logger.info("Prometheus metrics enabled at /metrics")
    except ImportError:
        logger.info("prometheus-flask-exporter not installed — metrics disabled")
    except Exception as exc:
        logger.warning("Failed to initialise Prometheus metrics: %s", exc)


def get_metrics():
    """Return the PrometheusMetrics instance, or None if unavailable."""
    return _metrics
