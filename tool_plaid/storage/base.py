"""Storage abstraction layer for tool-plaid"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Transaction:
    """Transaction data model."""
    transaction_id: str
    account_id: str
    amount: float
    date: str
    merchant_name: Optional[str]
    category: Optional[str]
    pending: bool


@dataclass
class AccountBalance:
    """Account balance data model."""
    account_id: str
    name: str
    mask: str
    type: str
    available: Optional[float]
    current: Optional[float]
    iso_currency_code: str
    timestamp: str


class StorageBackend(ABC):
    """Abstract storage backend interface."""

    @abstractmethod
    async def get_cursor(self, item_id: str) -> Optional[str]:
        """Get stored cursor for an item."""
        pass

    @abstractmethod
    async def set_cursor(self, item_id: str, cursor: str) -> None:
        """Store cursor for an item."""
        pass

    @abstractmethod
    async def add_transactions(self, item_id: str, transactions: List[Transaction]) -> None:
        """Add new transactions for an item."""
        pass

    @abstractmethod
    async def update_transaction(self, item_id: str, transaction: Transaction) -> None:
        """Update an existing transaction."""
        pass

    @abstractmethod
    async def remove_transactions(self, item_id: str, transaction_ids: List[str]) -> None:
        """Remove transactions by IDs."""
        pass

    @abstractmethod
    async def get_transactions(self, item_id: str) -> List[Transaction]:
        """Get all transactions for an item."""
        pass

    @abstractmethod
    async def set_balance(self, item_id: str, balance: AccountBalance) -> None:
        """Store account balance."""
        pass

    @abstractmethod
    async def get_balance(self, item_id: str, account_ids: Optional[List[str]] = None) -> Optional[AccountBalance]:
        """Get stored balance for an item."""
        pass
