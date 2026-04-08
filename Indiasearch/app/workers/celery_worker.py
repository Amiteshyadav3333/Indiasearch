# app/workers/celery_worker.py
# 🧵 Celery App — Background Worker Initialization
# ----------------------------------------
# Creates and configures the Celery app instance.
# Broker: Redis (CELERY_BROKER_URL)
# Result backend: Redis (CELERY_RESULT_BACKEND)
#
# Start worker:
#   celery -A app.workers.celery_worker.celery worker --loglevel=info -c 4
#   (c 4 = 4 concurrent worker processes)

# from celery import Celery
from app.config.settings import Settings


def make_celery():
    """
    Create and configure Celery app.
    Uses the app factory pattern to avoid circular imports.
    """
    # TODO:
    # celery_app = Celery(
    #     "indiasearch",
    #     broker=Settings.CELERY_BROKER_URL,
    #     backend=Settings.CELERY_RESULT_BACKEND,
    # )
    # celery_app.conf.update(
    #     task_serializer="json",
    #     result_serializer="json",
    #     accept_content=["json"],
    #     timezone="Asia/Kolkata",
    #     enable_utc=True,
    #     task_track_started=True,
    #     worker_max_tasks_per_child=100,  # Prevent memory leaks
    # )
    # return celery_app
    raise NotImplementedError("Initialize Celery with Redis broker")


# celery = make_celery()
