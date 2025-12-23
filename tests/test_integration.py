"""Comprehensive tests for Plaid integration"""

import pytest
import os
from pathlib import Path


def test_sdk_initialization():
    """Test that Plaid SDK can be initialized."""
    from plaid.configuration import Configuration
    from plaid.api_client import ApiClient
    from plaid.api.plaid_api import PlaidApi
    
    config = Configuration(
        host="https://sandbox.plaid.com",
        api_key={
            "clientId": os.getenv("PLAID_CLIENT_ID", ""),
            "secret": os.getenv("PLAID_SECRET", ""),
        },
    )
    
    api_client_obj = ApiClient(configuration=config)
    api_client = PlaidApi(api_client=api_client_obj)
    
    assert api_client is not None
    print("✅ Plaid SDK initialized successfully")
    print(f"   API Client type: {type(api_client)}")
    print(f"   Available methods: {[m for m in dir(api_client) if not m.startswith('_') and callable(getattr(api_client, m))]}")


def test_encryption():
    """Test encryption utilities."""
    from tool_plaid.utils.encryption import Encryptor
    
    encryptor = Encryptor("test_key_32_bytes_long_for_testing_purposes_only")
    
    data = "sensitive_data"
    encrypted = encryptor.encrypt(data)
    
    assert encrypted != data
    assert len(encrypted) > 0
    
    decrypted = encryptor.decrypt(encrypted)
    assert decrypted == data
    
    print("✅ Encryption working correctly")
    print(f"   Encrypted: {encrypted[:50]}...")
    print(f"   Decrypted: {decrypted}")


def test_config_loading():
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
    
    print("✅ Configuration loading successful")
    print(f"   PLAID_ENV: {config.PLAID_ENV}")
    print(f"   PLAID_CLIENT_ID: {config.PLAID_CLIENT_ID}")
    print(f"   Is Sandbox: {config.is_sandbox}")


if __name__ == "__main__":
    import sys
    
    # Load .env.agent file if exists
    env_file = Path(__file__).parent.parent / ".env.agent"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    
    print("\n" + "="*50)
    print("Running Plaid Tool Integration Tests")
    print("="*50)
    print("\n")
    
    test_sdk_initialization()
    print("\n")
    
    test_encryption()
    print("\n")
    
    test_config_loading()
    print("\n")
    
    print("="*50)
    print("\n✅ All tests passed!")
    print("\nNext: Implement Plaid API client wrapper with async methods")
