"""
Structured logging configuration.

Provides consistent, parseable log output across all modules.
Configurable via LOG_LEVEL environment variable.
"""

import logging
import os
import json
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """JSON-structured log formatter for production.

    Falls back to standard format for local dev when LOG_FORMAT != "json".
    """

    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


# Configure based on environment
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("LOG_FORMAT", "standard")  # "json" for production

# Root logger setup
root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Clear existing handlers to avoid duplicate output
root_logger.handlers.clear()

handler = logging.StreamHandler()

if LOG_FORMAT == "json":
    handler.setFormatter(StructuredFormatter())
else:
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

root_logger.addHandler(handler)

# Quiet noisy third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("google_adk").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.INFO)

logger = logging.getLogger("core.logger")
