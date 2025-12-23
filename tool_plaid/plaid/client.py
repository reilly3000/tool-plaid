"""Plaid API client wrapper (async)"""

import asyncio
import logging
from typing import List, Optional

from plaid.api import plaid_api
from plaid.model.transactions import TransactionsSyncResponse as PlaidTransactionsSyncResponse
from plaid.model.accounts import AccountsBalanceGetResponse

from tool_plaid.config import Config
from tool_plaid.plaid.models import Transaction, AccountBalance

# Import compatibility for older plaid-python versions
try:
    from plaid.model.transactions import TransactionsSyncResponse as PlaidTransactionsSyncResponseV18
    PlaidTransactionsSyncResponse = PlaidTransactionsSyncResponseV18
except ImportError:
    pass  # Use default import

logger = logging.getLogger(__name__)


class PlaidClient:
    """Async wrapper around Plaid Python SDK."""

    def __init__(self, config: Config):
        """
        Initialize Plaid client.

        Args:
            config: Application configuration
        """
        self.config = config

        configuration = plaid_api.Configuration(
            host=self._get_host(),
            api_key={"clientId": config.PLAID_CLIENT_ID, "secret": config.PLAID_SECRET},
        )

        self.api_client = plaid_api.PlaidApi(configuration)
        logger.info(f"PlaidClient initialized for {config.PLAID_ENV}")

    def _get_host(self) -> str:
        """Get Plaid API host based on environment."""
        if self.config.is_sandbox:
            return "https://sandbox.plaid.com"
        return "https://production.plaid.com"  # Placeholder for prod

    async def get_access_token(self, public_token: str) -> str:
        """
        Exchange public token for access token.

        Args:
            public_token: Public token from Plaid Link

        Returns:
            Access token

        Raises:
            Exception: If exchange fails
        """
        logger.info("Exchanging public token for access token")

        try:
            response = await asyncio.to_thread(
                self.api_client.item_public_token_exchange,
                {"public_token": public_token},
            )
            return response["access_token"]
        except Exception as e:
            logger.error(f"Failed to exchange public token: {e}")
            raise

    async def sync_transactions(
        self,
        access_token: str,
        cursor: Optional[str] = None,
        count: int = 500,
    ) -> dict:
        """
        Sync transactions using cursor-based approach.

        Args:
            access_token: Plaid access token
            cursor: Stored cursor for incremental sync
            count: Number of transactions to fetch

        Returns:
            Dictionary with added, modified, removed, next_cursor, has_more, item_status
        """
        logger.debug(f"Syncing transactions with cursor: {cursor}")

        try:
            response: PlaidTransactionsSyncResponse = await asyncio.to_thread(
                self.api_client.transactions_sync,
                {"access_token": access_token, "cursor": cursor, "count": count},
            )

            # Convert Plaid models to our schema
            added = [
                Transaction(
                    transaction_id=tx.transaction_id,
                    account_id=tx.account_id,
                    amount=float(tx.amount),
                    date=tx.date,
                    merchant_name=tx.merchant_name or "",
                    category=tx.category or "",
                    pending=tx.pending or False,
                )
                for tx in response["added"]
            ]

            modified = [
                Transaction(
                    transaction_id=tx.transaction_id,
                    account_id=tx.account_id,
                    amount=float(tx.amount),
                    date=tx.date,
                    merchant_name=tx.merchant_name or "",
                    category=tx.category or "",
                    pending=tx.pending or False,
                )
                for tx in response["modified"]
            ]

            removed = [tx.transaction_id for tx in response["removed"]]

            return {
                "added": added,
                "modified": modified,
                "removed": removed,
                "next_cursor": response.get("next_cursor", ""),
                "has_more": response.get("has_more", False),
                "item_status": response.get("item_status", "UNKNOWN"),
            }

        except Exception as e:
            logger.error(f"Failed to sync transactions: {e}")
            raise

    async def get_balance(
        self,
        access_token: str,
        account_ids: Optional[List[str]] = None,
    ) -> List[AccountBalance]:
        """
        Get account balances.

        Args:
            access_token: Plaid access token
            account_ids: Optional list of account IDs to filter

        Returns:
            List of account balances
        """
        logger.debug("Fetching account balances")

        try:
            response: AccountsBalanceGetResponse = await asyncio.to_thread(
                self.api_client.accounts_balance_get,
                {"access_token": access_token},
            )

            balances = []
            for account in response["accounts"]:
                # Filter by account_ids if provided
                if account_ids and account["account_id"] not in account_ids:
                    continue

                balances.append(
                    AccountBalance(
                        account_id=account["account_id"],
                        name=account["name"],
                        mask=account["mask"],
                        type=account["type"],
                        available=account["balances"].get("available"),
                        current=account["balances"].get("current"),
                        iso_currency_code=account["balances"].get("iso_currency_code", "USD"),
                    )
                )

            logger.info(f"Retrieved {len(balances)} account balances")
            return balances

        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise

    async def refresh_transactions(self, access_token: str) -> None:
        """
        Trigger transaction refresh for an item.

        Args:
            access_token: Plaid access token
        """
        logger.info("Triggering transaction refresh")

        try:
            await asyncio.to_thread(
                self.api_client.transactions_refresh,
                {"access_token": access_token},
            )
        except Exception as e:
            logger.error(f"Failed to refresh transactions: {e}")
            raise
