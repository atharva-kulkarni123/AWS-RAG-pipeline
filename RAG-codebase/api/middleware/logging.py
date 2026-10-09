import time
import uuid
import json
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


def setup_logging():
    """
    Emit structured JSON logs — CloudWatch Logs Insights
    can query these fields directly with filter @message.
    """
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log = {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
            }
            # merge any extra={} fields the caller passed
            for key, val in record.__dict__.items():
                if key not in (
                    "args", "asctime", "created", "exc_info",
                    "exc_text", "filename", "funcName", "id",
                    "levelname", "levelno", "lineno", "message",
                    "module", "msecs", "msg", "name", "pathname",
                    "process", "processName", "relativeCreated",
                    "stack_info", "thread", "threadName"
                ):
                    log[key] = val
            return json.dumps(log)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.root.setLevel(logging.INFO)
    logging.root.handlers = [handler]


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start = time.time()

        # attach request_id so route handlers can log it
        request.state.request_id = request_id

        logger.info(
            "request_start",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            }
        )

        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)

        logger.info(
            "request_complete",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        )

        response.headers["X-Request-ID"] = request_id
        return response