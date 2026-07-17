import json
import logging
import os
from contextvars import ContextVar
from typing import Any

# Thread-local / async task correlation ID tracker
CORRELATION_ID_VAR = ContextVar("correlation_id", default="")

class StructuredJSONFormatter(logging.Formatter):
    """Log formatter that outputs log lines as parseable JSON objects.

    Automatically injects the current correlation ID if present in the async context.
    """
    def format(self, record):
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": CORRELATION_ID_VAR.get() or "none",
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Standard attributes of LogRecord to exclude from the custom extra payload
        std_fields = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'msg', 'name', 'pathname', 'process', 'processName',
            'relativeCreated', 'stack_info', 'thread', 'threadName'
        }
        extra = {k: v for k, v in record.__dict__.items() if k not in std_fields}
        if extra:
            log_entry["extra"] = extra

        return json.dumps(log_entry)

def setup_logging():
    """Initialise global logging formatter based on the LOG_FORMAT env var."""
    log_format = os.environ.get("LOG_FORMAT", "text").strip().lower()
    text_format = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

    root_logger = logging.getLogger()

    if root_logger.handlers:
        for handler in root_logger.handlers:
            if log_format == "json":
                handler.setFormatter(StructuredJSONFormatter())
            else:
                handler.setFormatter(logging.Formatter(text_format))
    else:
        handler = logging.StreamHandler()
        if log_format == "json":
            handler.setFormatter(StructuredJSONFormatter())
        else:
            handler.setFormatter(logging.Formatter(text_format))
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
