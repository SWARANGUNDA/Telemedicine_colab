"""
celery_app.py — Celery App Instance Configuration for Asynchronous Background Tasks.
"""

import os
from celery import Celery

import socket

def resolve_redis_url():
    env_url = os.getenv("REDIS_URL")
    if env_url:
        return env_url
    try:
        socket.gethostbyname("redis")
        return "redis://redis:6379/0"
    except Exception:
        try:
            s = socket.socket()
            s.settimeout(1)
            s.connect(("localhost", 6380))
            s.close()
            return "redis://localhost:6380/0"
        except Exception:
            return "redis://localhost:6379/0"

REDIS_URL = resolve_redis_url()

celery_app = Celery(
    "telemed_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.backend.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    broker_connection_retry_on_startup=True
)
