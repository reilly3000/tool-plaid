"""CLI entry point for tool-plaid MCP server"""

import sys

from tool_plaid.server import main

if __name__ == "__main__":
    sys.exit(main())
