"""Logging helpers for the Miss Westie bot."""

from __future__ import annotations

import logging
from typing import Iterable


DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging(level: int = logging.INFO, handlers: Iterable[logging.Handler] | None = None) -> None:
    """Configure the root logger with a consistent format.

    Parameters
    ----------
    level:
        The minimum logging level to emit. ``logging.INFO`` by default.
    handlers:
        Optional iterable of custom handlers to register. If omitted a
        standard :class:`logging.StreamHandler` is installed.
    """

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicate messages when the bot reloads
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    if handlers:
        for handler in handlers:
            handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
            root_logger.addHandler(handler)
    else:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        root_logger.addHandler(stream_handler)


__all__ = ["configure_logging", "DEFAULT_LOG_FORMAT"]
