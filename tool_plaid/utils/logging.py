"""Logging configuration for tool-plaid"""

import logging
import sys
from pathlib import Path


def setup_logging(log_file: str = "plaid_tool.log") -> None:
    """
    Configure logging to write to file instead of stdout/stderr.

    This avoids interference with MCP communication channel.
    """
    log_path = Path.cwd() / log_file

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stderr),  # Errors to stderr only
        ],
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured to {log_path}")
