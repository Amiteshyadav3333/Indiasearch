# app/utils/logger.py
# 🧰 Logger — Centralized Structured Logging
# ----------------------------------------
# All modules should import 'logger' from here instead of using print().
# Uses Python's logging module with structured JSON format for production.
#
# Usage:
#   from app.utils.logger import logger
#   logger.info("Search query received", extra={"query": q, "lang": lang})
#   logger.error("Elasticsearch failed", exc_info=True)

import logging
import os
import json

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


class JsonFormatter(logging.Formatter):
    """Format logs as JSON for production log aggregators (Datadog, Railway Logs)."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("indiasearch")
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    handler = logging.StreamHandler()
    env = os.environ.get("FLASK_ENV", "production")
    if env == "production":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(module)s: %(message)s")
        )

    if not logger.handlers:
        logger.addHandler(handler)
    return logger


# Single shared logger instance — import this everywhere
logger = _setup_logger()
