# app/workers/__init__.py
# 🧵 Workers — Background Jobs (Celery)
# ----------------------------------------
# Async job processing using Celery + Redis as broker.
# Workers run as a SEPARATE PROCESS from the Flask API.
#
# Start worker (locally):
#   celery -A app.workers.celery_worker.celery worker --loglevel=info
#
# Railway deployment:
#   Add a second dyno/service with the celery start command.
