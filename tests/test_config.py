"""Unit tests for configuration settings."""
import os
from app.config import Settings


def test_settings_default_values():
    """Test that settings have correct default values."""
    settings = Settings()
    
    assert settings.nasa_api_key == "DEMO_KEY"
    assert settings.redis_host == "redis"
    assert settings.redis_port == 6379
    assert settings.redis_db == 0
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000
    assert settings.use_mock is False
    assert settings.max_cached_list_size == 50
    assert settings.cache_ttl_recent == 0
    assert settings.cache_ttl_historical == 365
    assert settings.cache_recent_days_threshold == 7


def test_settings_from_env(monkeypatch):
    """Test that settings can be loaded from environment variables."""
    monkeypatch.setenv("NASA_API_KEY", "test_key")
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6380")
    monkeypatch.setenv("USE_MOCK", "true")
    monkeypatch.setenv("CACHE_TTL_HISTORICAL", "730")
    
    settings = Settings()
    
    assert settings.nasa_api_key == "test_key"
    assert settings.redis_host == "localhost"
    assert settings.redis_port == 6380
    assert settings.use_mock is True
    assert settings.cache_ttl_historical == 730


def test_settings_cache_configuration():
    """Test cache-related settings."""
    settings = Settings()
    
    # Test that cache settings are integers
    assert isinstance(settings.cache_ttl_recent, int)
    assert isinstance(settings.cache_ttl_historical, int)
    assert isinstance(settings.cache_recent_days_threshold, int)
    
    # Test reasonable defaults
    assert settings.cache_ttl_recent >= 0  # 0 means indefinite
    assert settings.cache_ttl_historical > 0  # Must be positive
    assert settings.cache_recent_days_threshold > 0  # Must be positive
