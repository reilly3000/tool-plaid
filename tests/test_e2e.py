"""
End-to-End Test for Plaid MCP Tool

This script tests the complete flow:
1. Exchange public_token for access_token
2. Store access_token with item_id
3. Sync transactions
4. Get balance

To run:
1. Get a public_token from Plaid Link (https://plaid.com/docs/quickstart/)
2. Run: python test_e2e.py <public_token>
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tool_plaid.config import Config
from tool_plaid.plaid.client import PlaidClient
from tool_plaid.auth.tokens import TokenManager
from tool_plaid.storage.file import FileStorage


async def test_e2e_flow(public_token: str):
    """Test end-to-end flow with Plaid API."""

    print("=" * 60)
    print("Plaid MCP Tool - End-to-End Test")
    print("=" * 60)
    print()

    # Load configuration
    print("📋 Loading configuration...")
    config = Config.load()
    print(f"✅ Environment: {config.PLAID_ENV}")
    print(f"✅ Storage: {config.STORAGE_MODE}")
    print(f"✅ Data dir: {config.data_dir}")
    print()

    # Initialize components
    print("🔧 Initializing components...")
    plaid_client = PlaidClient(config)
    token_manager = TokenManager(config.data_dir, config.ENCRYPTION_KEY)
    storage = FileStorage(config.data_dir)
    print("✅ Plaid client initialized")
    print("✅ Token manager initialized")
    print("✅ Storage backend initialized")
    print()

    # Step 1: Exchange public token for access token
    print("🔄 Step 1: Exchanging public token for access token...")
    print(f"   Public token: {public_token[:20]}...")

    try:
        access_token = await plaid_client.exchange_public_token(public_token)
        print(f"✅ Access token received: {access_token[:20]}...")
        print()

        # Generate item_id from token (simplified - in production use actual item_id from response)
        item_id = f"test_item_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    except Exception as e:
        print(f"❌ Failed to exchange public token: {e}")
        print()
        print("💡 Make sure you're using a valid public_token from Plaid Link")
        print("   Get one from: https://plaid.com/docs/quickstart/")
        return False

    # Step 2: Store access token
    print("💾 Step 2: Storing access token...")
    try:
        await token_manager.store_token(
            access_token=access_token,
            item_id=item_id,
            metadata={"institution": "Test Institution", "linked_at": datetime.utcnow().isoformat()}
        )
        print(f"✅ Token stored for item_id: {item_id}")
        print()

    except Exception as e:
        print(f"❌ Failed to store token: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Sync transactions
    print("📊 Step 3: Syncing transactions...")
    try:
        result = await plaid_client.sync_transactions(
            access_token=access_token,
            cursor=None,
            count=100,
            days_requested=30
        )

        print(f"✅ Transactions synced successfully!")
        print(f"   Added: {len(result['added'])}")
        print(f"   Modified: {len(result['modified'])}")
        print(f"   Removed: {len(result['removed'])}")
        print(f"   Has more: {result['has_more']}")
        print(f"   Item status: {result['item_status']}")
        print()

        # Store cursor
        await storage.set_cursor(item_id, result['next_cursor'])
        print(f"✅ Cursor stored: {result['next_cursor'][:30]}...")
        print()

    except Exception as e:
        print(f"❌ Failed to sync transactions: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: Get balance
    print("💰 Step 4: Getting account balances...")
    try:
        balances = await plaid_client.get_balance(access_token=access_token)
        print(f"✅ Balance retrieved successfully!")
        print(f"   Accounts: {len(balances)}")
        print()

        for i, balance in enumerate(balances, 1):
            print(f"   Account {i}:")
            print(f"      Name: {balance.name}")
            print(f"      Mask: {balance.mask}")
            print(f"      Type: {balance.type}")
            print(f"      Available: ${balance.available:.2f}" if balance.available else "      Available: N/A")
            print(f"      Current: ${balance.current:.2f}" if balance.current else "      Current: N/A")
            print(f"      Currency: {balance.iso_currency_code}")
        print()

    except Exception as e:
        print(f"❌ Failed to get balance: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Test token retrieval
    print("🔓 Step 5: Retrieving stored token...")
    try:
        retrieved_token = await token_manager.get_token(item_id)
        if retrieved_token == access_token:
            print(f"✅ Token retrieved successfully!")
            print(f"   Matches original: Yes")
        else:
            print(f"⚠️  Token retrieved but doesn't match!")
        print()

    except Exception as e:
        print(f"❌ Failed to retrieve token: {e}")
        return False

    # Summary
    print("=" * 60)
    print("✅ END-TO-END TEST SUCCESSFUL!")
    print("=" * 60)
    print()
    print(f"Item ID: {item_id}")
    print(f"Transactions synced: {len(result['added']) + len(result['modified'])}")
    print(f"Accounts retrieved: {len(balances)}")
    print()
    print("💡 You can now test the MCP tools:")
    print(f"   sync_transactions(item_id='{item_id}')")
    print(f"   get_balance(item_id='{item_id}')")
    print()
    print("To clean up:")
    print(f"   rm -rf {config.data_dir / 'items' / item_id}")
    print()

    return True


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_e2e.py <public_token>")
        print()
        print("Get a public_token from Plaid Link:")
        print("  https://plaid.com/docs/quickstart/")
        print()
        print("For testing, you can use Plaid's Sandbox environment")
        print("with test credentials.")
        sys.exit(1)

    public_token = sys.argv[1]
    success = asyncio.run(test_e2e_flow(public_token))

    if success:
        sys.exit(0)
    else:
        print()
        print("❌ End-to-end test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
