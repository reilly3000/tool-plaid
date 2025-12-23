"""MCP server for Plaid"""

import logging

from tool_plaid.utils.logging import setup_logging

logger = logging.getLogger(__name__)

# Setup file-based logging to avoid stdout/stderr interference
setup_logging()

def main() -> None:
    """Main entry point for testing."""
    try:
        logger.info("Starting Plaid MCP Tool server (testing)...")
        
        from plaid.configuration import Configuration
        from plaid.api.plaid_api import PlaidApi
        
        # Create configuration with keyword arguments
        config = Configuration(
            host="https://sandbox.plaid.com",
            api_key={
                "clientId": os.getenv("PLAID_CLIENT_ID", ""),
                "secret": os.getenv("PLAID_SECRET", ""),
            },
        )
        
        # Create API client
        api_client = PlaidApi(configuration=config)
        
        logger.info("Plaid SDK initialized successfully")
        logger.info(f"API Client type: {type(api_client)}")
        logger.info(f"API Client methods: {len([m for m in dir(api_client) if not m.startswith('_') and callable(getattr(api_client, m))])}")
        
        print("SUCCESS: Plaid SDK working!")
        print("Next step: Implementing tools with actual API calls")
        
    except ImportError as e:
        logger.error(f"Failed to import Plaid SDK: {e}")
        print(f"ERROR: {e}")
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
