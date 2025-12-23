"""Test configuration management"""

import os
from pathlib import Path

import pytest


@pytest.fixture
def test_env():
    """Load test environment variables."""
    env_file = Path(__file__).parent.parent / ".env.agent"
    
    # Load env file
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key.strip()] = value.strip()
    
    return os.environ


@pytest.fixture
def config(test_env):
    """Test configuration loading."""
    from tool_plaid.config import Config
    
    config = Config.load()
    
    assert config.PLAID_ENV == "sandbox"
    assert config.PLAID_CLIENT_ID == "62eacf714206f30013d6e722"
    assert config.PLAID_SECRET == "6f85aa5808d484246313470945c515"
    assert len(config.ENCRYPTION_KEY) >= 32
    assert config.STORAGE_MODE == "file"
    assert config.MCP_TRANSPORT == "stdio"
    assert config.BALANCE_CACHE_TTL == 300
    
    assert config.is_sandbox is True
    assert config.validate() is None
    
    return config


def test_sdk_initialization(config):
    """Test that Plaid SDK can be initialized."""
    from plaid.configuration import Configuration
    from plaid.api_client import ApiClient
    from plaid.api.plaid_api import PlaidApi
    
    # Create configuration using keyword arguments
    plaid_config = Configuration(
        host="https://sandbox.plaid.com",
        api_key={
            "clientId": config.PLAID_CLIENT_ID,
            "secret": config.PLAID_SECRET,
        },
    )
    
    # Create API client
    api_client_obj = ApiClient(configuration=plaid_config)
    api_client = PlaidApi(api_client=api_client_obj)
    
    assert api_client is not None
    assert hasattr(api_client, "api_client")
    
    print("✓ Plaid SDK initialization successful")
    print(f"  API Client type: {type(api_client)}")


def test_encryption(config):
    """Test encryption utilities."""
    from tool_plaid.utils.encryption import Encryptor
    
    encryptor = Encryptor(config.ENCRYPTION_KEY)
    
    data = "sensitive_data"
    encrypted = encryptor.encrypt(data)
    
    assert encrypted != data
    assert len(encrypted) > 0
    
    decrypted = encryptor.decrypt(encrypted)
    assert decrypted == data
    
    print("✓ Encryption working correctly")


if __name__ == "__main__":
    import sys
    
    # Set up test environment
    env_file = Path(__file__).parent.parent / ".env.agent"
    
    print("Loading test environment from .env.agent...")
    
    # Load env file
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key.strip()] = value.strip()
    
    print("\nRunning tests...\n")
    
    from tool_plaid.config import Config
    config = Config.load()
    
    test_sdk_initialization(config)
    test_encryption(config)
    
    print("\n✅ All tests passed!")
