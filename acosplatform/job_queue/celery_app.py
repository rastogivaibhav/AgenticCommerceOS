# acosplatform/job_queue/celery_app.py
"""
Celery application configuration.

Configures Celery for async task execution with Redis as the message broker.
"""

import os
from celery import Celery

# Get Redis URL from environment or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "acos_job_queue",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=86400,  # 24 hours
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 min soft limit
)
