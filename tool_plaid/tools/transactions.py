"""MCP Tools for Plaid"""

import logging
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from tool_plaid.plaid.client import PlaidClient
from tool_plaid.plaid.models import Transaction, AccountBalance
from tool_plaid.storage.base import StorageBackend
from tool_plaid.storage.file import FileStorage
from tool_plaid.auth.tokens import TokenManager
from tool_plaid.config import Config

logger = logging.getLogger(__name__)


class SyncTransactionsInput(BaseModel):
    """Input for sync_transactions tool."""
    item_id: str = Field(description="Plaid item identifier")
    force_refresh: bool = Field(default=False, description="Trigger Plaid refresh")
    days_requested: Optional[int] = Field(default=90, ge=1, le=730, description="Days of history")


class SyncTransactionsResponse(BaseModel):
    """Response for sync_transactions tool."""
    added: List[Transaction] = Field(default_factory=list)
    modified: List[Transaction] = Field(default_factory=list)
    removed: List[str] = Field(default_factory=list, description="Transaction IDs")
    next_cursor: str = Field(default="")
    has_more: bool = Field(default=False)
    item_status: str = Field(default="")
    summary: str = Field(default="")


class GetBalanceInput(BaseModel):
    """Input for get_balance tool."""
    item_id: str = Field(description="Plaid item identifier")
    account_ids: Optional[List[str]] = Field(default=None, description="Filter accounts")
    force_refresh: bool = Field(default=False, description="Bypass cache")


class GetBalanceResponse(BaseModel):
    """Response for get_balance tool."""
    balances: List[AccountBalance] = Field(default_factory=list)
    cached: bool = Field(default=False)
    timestamp: str = Field(default="")


async def sync_transactions(
    item_id: str,
    force_refresh: bool = False,
    days_requested: Optional[int] = 90,
) -> SyncTransactionsResponse:
    """
    Sync transactions from Plaid using cursor-based incremental updates.

    Args:
        item_id: Plaid item identifier
        force_refresh: Trigger Plaid refresh
        days_requested: Days of history

    Returns:
        SyncTransactionsResponse with added, modified, removed transactions
    """
    logger.info(f"sync_transactions called for item_id: {item_id}")

    config = Config()
    token_manager = TokenManager(config.data_dir, config.ENCRYPTION_KEY)
    storage = FileStorage(config.data_dir)
    plaid_client = PlaidClient(config)

    # Get access token
    access_token = await token_manager.get_token(item_id)
    if not access_token:
        return SyncTransactionsResponse(
            item_status="ITEM_NOT_FOUND",
            summary=f"Item {item_id} not found or not linked",
        )

    # Trigger refresh if requested
    if force_refresh:
        try:
            await plaid_client.refresh_transactions(access_token)
            logger.info(f"Refreshed transactions for item {item_id}")
        except Exception as e:
            logger.error(f"Failed to refresh transactions: {e}")

    # Get current cursor
    cursor = await storage.get_cursor(item_id)

    # Sync transactions
    try:
        if days_requested:
            result = await plaid_client.sync_transactions(
                access_token=access_token,
                cursor=cursor,
                count=500,
                days_requested=days_requested,
            )
        else:
            result = await plaid_client.sync_transactions(
                access_token=access_token,
                cursor=cursor,
                count=500,
            )
    except Exception as e:
        logger.error(f"Failed to sync transactions: {e}")
        return SyncTransactionsResponse(
            item_status="ERROR",
            summary=f"Failed to sync: {str(e)}",
        )

    # Store updated cursor
    await storage.set_cursor(item_id, result["next_cursor"])

    # Store transactions
    if result["added"]:
        await storage.add_transactions(item_id, result["added"])

    if result["modified"]:
        for tx in result["modified"]:
            await storage.update_transaction(item_id, tx)

    if result["removed"]:
        await storage.remove_transactions(item_id, result["removed"])

    # Build summary
    summary_parts = []
    if result["added"]:
        summary_parts.append(f"Added {len(result['added'])}")
    if result["modified"]:
        summary_parts.append(f"Modified {len(result['modified'])}")
    if result["removed"]:
        summary_parts.append(f"Removed {len(result['removed'])}")

    summary = ", ".join(summary_parts) + " transactions"

    logger.info(f"sync_transactions completed: {summary}")

    return SyncTransactionsResponse(
        added=result["added"],
        modified=result["modified"],
        removed=result["removed"],
        next_cursor=result["next_cursor"],
        has_more=result["has_more"],
        item_status=result["item_status"],
        summary=summary,
    )


async def get_balance(
    item_id: str,
    account_ids: Optional[List[str]] = None,
    force_refresh: bool = False,
) -> GetBalanceResponse:
    """
    Get account balances with intelligent caching.

    Args:
        item_id: Plaid item identifier
        account_ids: Filter specific accounts
        force_refresh: Bypass cache

    Returns:
        GetBalanceResponse with balances and caching metadata
    """
    logger.info(f"get_balance called for item_id: {item_id}")

    config = Config()
    token_manager = TokenManager(config.data_dir, config.ENCRYPTION_KEY)
    storage = FileStorage(config.data_dir)
    plaid_client = PlaidClient(config)

    # Get access token
    access_token = await token_manager.get_token(item_id)
    if not access_token:
        return GetBalanceResponse(
            cached=False,
            timestamp=datetime.utcnow().isoformat(),
        )

    # Check cache first
    if not force_refresh:
        cached = await storage.get_balance(item_id, account_ids)
        if cached:
            logger.info("Returning cached balance")
            return GetBalanceResponse(
                balances=[cached],
                cached=True,
                timestamp=cached.timestamp,
            )

    # Fetch from Plaid
    try:
        balances = await plaid_client.get_balance(
            access_token=access_token,
            account_ids=account_ids,
        )
    except Exception as e:
        logger.error(f"Failed to get balance: {e}")
        return GetBalanceResponse(
            cached=False,
            timestamp=datetime.utcnow().isoformat(),
        )

    # Store in cache
    if balances:
        await storage.set_balance(item_id, balances[0])

    timestamp = datetime.utcnow().isoformat()

    logger.info(f"get_balance completed: {len(balances)} accounts")

    return GetBalanceResponse(
        balances=balances,
        cached=False,
        timestamp=timestamp,
    )
