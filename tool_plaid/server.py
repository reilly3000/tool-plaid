"""MCP server for Plaid"""

import logging
import os
from mcp.server.fastmcp import FastMCP

from tool_plaid.utils.logging import setup_logging
from tool_plaid.config import Config
from tool_plaid.tools.transactions import sync_transactions, get_balance

# Setup file-based logging to avoid stdout/stderr interference
setup_logging()

logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("Plaid Tool", instructions="Sync transactions and get account balances from Plaid")

# Register tools
mcp.tool()(sync_transactions)
mcp.tool()(get_balance)


def main() -> None:
    """Main entry point for the MCP server."""
    try:
        config = Config.load()
        config.validate()

        logger.info(f"Starting Plaid MCP Tool in {config.PLAID_ENV} mode")
        logger.info(f"Storage mode: {config.STORAGE_MODE}")
        logger.info(f"Transport: {config.MCP_TRANSPORT}")

        # Run MCP server with configured transport
        mcp.run(transport=config.MCP_TRANSPORT)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise


if __name__ == "__main__":
    main()
