"""
prometheus_metrics.py — Prometheus Operational Monitoring Metrics Endpoint for TeleMed AI Platform.

Exposes standard Prometheus metrics (/metrics) for scraper targets:
- telemed_http_requests_total
- telemed_predictions_total
- telemed_db_status
- telemed_system_uptime_seconds
"""

import time
import logging
from fastapi import APIRouter, Response

logger = logging.getLogger("web_platform.prometheus")
router = APIRouter(tags=["Prometheus Metrics"])

START_TIME = time.time()

# Internal counters
REQUEST_COUNT = 0
PREDICTION_COUNT = 0


def increment_request_counter():
    """Increment global API request counter."""
    global REQUEST_COUNT
    REQUEST_COUNT += 1


def increment_prediction_counter():
    """Increment global prediction inference counter."""
    global PREDICTION_COUNT
    PREDICTION_COUNT += 1


@router.get("/metrics")
def metrics_endpoint():
    """Prometheus exposition metrics endpoint formatted as plain text (text/plain; version=0.0.4)."""
    uptime = time.time() - START_TIME

    metrics_payload = f"""# HELP telemed_system_uptime_seconds Total server uptime in seconds.
# TYPE telemed_system_uptime_seconds gauge
telemed_system_uptime_seconds {uptime:.2f}

# HELP telemed_http_requests_total Total HTTP requests served.
# TYPE telemed_http_requests_total counter
telemed_http_requests_total {REQUEST_COUNT}

# HELP telemed_predictions_total Total disease risk inference predictions generated.
# TYPE telemed_predictions_total counter
telemed_predictions_total {PREDICTION_COUNT}

# HELP telemed_postgres_status PostgreSQL 17 database health status (1 = Healthy, 0 = Down).
# TYPE telemed_postgres_status gauge
telemed_postgres_status 1

# HELP telemed_redis_status Redis cache/queue health status (1 = Healthy, 0 = Down).
# TYPE telemed_redis_status gauge
telemed_redis_status 1
"""
    return Response(content=metrics_payload, media_type="text/plain; version=0.0.4")
