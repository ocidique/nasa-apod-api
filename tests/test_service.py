"""Unit tests for NASA APOD service."""
import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from app.service import NASAAPODService
from app.config import Settings


@pytest.fixture
def service():
    """Create a NASAAPODService instance for testing."""
    return NASAAPODService()


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Settings()
    settings.use_mock = True
    settings.cache_ttl_recent = 0
    settings.cache_ttl_historical = 365
    settings.cache_recent_days_threshold = 7
    return settings


@pytest.mark.asyncio
async def test_service_initialization(service):
    """Test service initialization."""
    assert service.redis_client is None
    assert service.NASA_APOD_URL == "https://api.nasa.gov/planetary/apod"
    assert service.APOD_START_DATE == date(1995, 6, 16)


@pytest.mark.asyncio
async def test_get_next_date(service):
    """Test getting the next date."""
    current = date(2024, 1, 15)
    next_date = service.get_next_date(current)
    
    assert next_date == date(2024, 1, 16)


@pytest.mark.asyncio
async def test_get_next_date_today(service):
    """Test that next date is None for today."""
    today = date.today()
    next_date = service.get_next_date(today)
    
    assert next_date is None


@pytest.mark.asyncio
async def test_get_prev_date(service):
    """Test getting the previous date."""
    current = date(2024, 1, 15)
    prev_date = service.get_prev_date(current)
    
    assert prev_date == date(2024, 1, 14)


@pytest.mark.asyncio
async def test_get_prev_date_start_date(service):
    """Test that previous date is None for APOD start date."""
    start_date = date(1995, 6, 16)
    prev_date = service.get_prev_date(start_date)
    
    assert prev_date is None


@pytest.mark.asyncio
async def test_get_prev_date_before_start(service):
    """Test that previous date is None before APOD start date."""
    before_start = date(1995, 6, 15)
    prev_date = service.get_prev_date(before_start)
    
    assert prev_date is None


@pytest.mark.asyncio
async def test_fetch_apod_with_mock_data(service, mock_settings):
    """Test fetching APOD with mock data."""
    with patch('app.service.settings', mock_settings):
        # Initialize Redis connection (mock)
        service.redis_client = AsyncMock()
        service.redis_client.get = AsyncMock(return_value=None)
        service.redis_client.set = AsyncMock()
        service.redis_client.setex = AsyncMock()
        
        test_date = date(2024, 1, 15)
        result = await service.fetch_apod(test_date)
        
        assert result["date"] == "2024-01-15"
        assert "title" in result
        assert "explanation" in result
        assert "url" in result


@pytest.mark.asyncio
async def test_fetch_apod_from_cache(service):
    """Test fetching APOD from cache."""
    import json
    
    # Setup mock Redis client
    service.redis_client = AsyncMock()
    cached_data = {
        "date": "2024-01-15",
        "title": "Cached APOD",
        "explanation": "Cached explanation",
        "url": "https://example.com/cached.jpg",
        "media_type": "image"
    }
    service.redis_client.get = AsyncMock(return_value=json.dumps(cached_data))
    
    test_date = date(2024, 1, 15)
    result = await service.fetch_apod(test_date)
    
    assert result == cached_data
    service.redis_client.get.assert_called_once_with("apod:2024-01-15")


@pytest.mark.asyncio
async def test_cache_ttl_for_recent_apod(service, mock_settings):
    """Test that recent APODs are cached indefinitely."""
    from datetime import datetime
    
    with patch('app.service.settings', mock_settings):
        service.redis_client = AsyncMock()
        service.redis_client.set = AsyncMock()
        
        # Recent date (2 days ago)
        recent_date = date.today() - timedelta(days=2)
        data = {"date": recent_date.isoformat(), "title": "Recent APOD"}
        
        await service._store_in_cache(recent_date.isoformat(), data)
        
        # Should call set (indefinite) not setex (with expiration)
        service.redis_client.set.assert_called_once()


@pytest.mark.asyncio
async def test_cache_ttl_for_historical_apod(service, mock_settings):
    """Test that historical APODs are cached with TTL."""
    with patch('app.service.settings', mock_settings):
        service.redis_client = AsyncMock()
        service.redis_client.setex = AsyncMock()
        
        # Historical date (100 days ago)
        historical_date = date.today() - timedelta(days=100)
        data = {"date": historical_date.isoformat(), "title": "Historical APOD"}
        
        await service._store_in_cache(historical_date.isoformat(), data)
        
        # Should call setex (with expiration)
        service.redis_client.setex.assert_called_once()


@pytest.mark.asyncio
async def test_preload_recent_apods(service, mock_settings):
    """Test preloading recent APODs."""
    with patch('app.service.settings', mock_settings):
        service.redis_client = AsyncMock()
        service.redis_client.get = AsyncMock(return_value=None)
        service.redis_client.set = AsyncMock()
        service.redis_client.setex = AsyncMock()
        
        # Preload 3 days
        await service.preload_recent_apods(days=3)
        
        # Should have attempted to fetch 3 APODs
        # (calls to redis might be more due to caching logic)
        assert service.redis_client.get.call_count >= 3


@pytest.mark.asyncio
async def test_get_available_dates_empty(service):
    """Test getting available dates when cache is empty."""
    service.redis_client = AsyncMock()
    service.redis_client.scan = AsyncMock(return_value=(0, []))
    
    dates = await service.get_available_dates()
    
    assert dates == []


@pytest.mark.asyncio
async def test_get_available_dates_with_data(service):
    """Test getting available dates from cache."""
    service.redis_client = AsyncMock()
    # Mock SCAN to return some keys
    service.redis_client.scan = AsyncMock(
        return_value=(0, ["apod:2024-01-15", "apod:2024-01-16", "apod:2024-01-14"])
    )
    
    dates = await service.get_available_dates()
    
    # Should be sorted in reverse order (most recent first)
    assert dates == ["2024-01-16", "2024-01-15", "2024-01-14"]


@pytest.mark.asyncio
async def test_close_service(service):
    """Test closing the service."""
    service.redis_client = AsyncMock()
    service.redis_client.close = AsyncMock()
    
    await service.close()
    
    service.redis_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_close_service_no_client(service):
    """Test closing service when Redis client is None."""
    service.redis_client = None
    
    # Should not raise an exception
    await service.close()
