from __future__ import annotations

import copy
import os
import uvicorn
from uvicorn.config import LOGGING_CONFIG

from customer_support_agent.api.app_factory import create_app
from customer_support_agent.core.settings import get_settings

app = create_app()


def _build_log_config() -> dict:
    log_config = copy.deepcopy(LOGGING_CONFIG)
    log_config["root"] = {"handlers": ["default"], "level": "INFO"}
    loggers = log_config.setdefault("loggers", {})
    loggers["customer_support_agent"] = {
        "handlers": ["default"],
        "level": "INFO",
        "propagate": False,
    }
    return log_config


if __name__ == "__main__":
    settings = get_settings()
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", str(settings.api_port)))
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_config=_build_log_config(),
        log_level="info",
    )
