"""Unit tests for FastAPI endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import date
from unittest.mock import AsyncMock, patch
from app.main import app
from app.service import nasa_service


@pytest.fixture
async def client():
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def mock_service():
    """Mock NASA service for all tests."""
    # Mock initialize and close
    with patch.object(nasa_service, 'initialize', new_callable=AsyncMock), \
         patch.object(nasa_service, 'close', new_callable=AsyncMock), \
         patch.object(nasa_service, 'preload_recent_apods', new_callable=AsyncMock):
        yield


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_get_today_apod(client):
    """Test getting today's APOD."""
    mock_data = {
        "date": date.today().isoformat(),
        "title": "Test APOD",
        "explanation": "Test explanation",
        "url": "https://example.com/image.jpg",
        "media_type": "image"
    }
    
    with patch.object(nasa_service, 'fetch_apod', new_callable=AsyncMock, return_value=mock_data):
        response = await client.get("/api/apod/today")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test APOD"
        assert data["date"] == date.today().isoformat()


@pytest.mark.asyncio
async def test_get_apod_by_query_param(client):
    """Test getting APOD by date query parameter."""
    test_date = "2024-01-15"
    mock_data = {
        "date": test_date,
        "title": "Test APOD",
        "explanation": "Test explanation",
        "url": "https://example.com/image.jpg",
        "media_type": "image"
    }
    
    with patch.object(nasa_service, 'fetch_apod', new_callable=AsyncMock, return_value=mock_data):
        response = await client.get(f"/api/apod?date={test_date}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == test_date
        assert data["title"] == "Test APOD"


@pytest.mark.asyncio
async def test_get_apod_by_path_param(client):
    """Test getting APOD by date path parameter."""
    test_date = "2024-01-15"
    mock_data = {
        "date": test_date,
        "title": "Test APOD Path",
        "explanation": "Test explanation",
        "url": "https://example.com/image.jpg",
        "media_type": "image"
    }
    
    with patch.object(nasa_service, 'fetch_apod', new_callable=AsyncMock, return_value=mock_data):
        response = await client.get(f"/api/apod/{test_date}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == test_date
        assert data["title"] == "Test APOD Path"


@pytest.mark.asyncio
async def test_get_apod_invalid_date_format(client):
    """Test getting APOD with invalid date format."""
    response = await client.get("/api/apod?date=invalid-date")
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid date format" in data["detail"]


@pytest.mark.asyncio
async def test_get_apod_date_before_start(client):
    """Test getting APOD with date before APOD start date."""
    response = await client.get("/api/apod?date=1990-01-01")
    
    assert response.status_code == 400
    data = response.json()
    assert "must be on or after" in data["detail"]


@pytest.mark.asyncio
async def test_get_apod_future_date(client):
    """Test getting APOD with future date."""
    from datetime import timedelta
    future_date = (date.today() + timedelta(days=10)).isoformat()
    
    response = await client.get(f"/api/apod?date={future_date}")
    
    assert response.status_code == 400
    data = response.json()
    assert "Cannot request future dates" in data["detail"]


@pytest.mark.asyncio
async def test_get_apod_with_navigation_links(client):
    """Test that APOD response includes navigation links."""
    test_date = "2024-01-15"
    mock_data = {
        "date": test_date,
        "title": "Test APOD",
        "explanation": "Test explanation",
        "url": "https://example.com/image.jpg",
        "media_type": "image"
    }
    
    with patch.object(nasa_service, 'fetch_apod', new_callable=AsyncMock, return_value=mock_data):
        response = await client.get(f"/api/apod?date={test_date}")
        
        assert response.status_code == 200
        data = response.json()
        assert "next_date" in data
        assert "prev_date" in data
        # Should have both next and prev for middle dates
        assert data["next_date"] is not None
        assert data["prev_date"] is not None


@pytest.mark.asyncio
async def test_list_cached_apods(client):
    """Test listing cached APODs."""
    mock_dates = ["2024-01-15", "2024-01-14", "2024-01-13"]
    mock_apod = {
        "date": "2024-01-15",
        "title": "Test APOD",
        "explanation": "Test explanation",
        "url": "https://example.com/image.jpg",
        "media_type": "image"
    }
    
    with patch.object(nasa_service, 'get_available_dates', new_callable=AsyncMock, return_value=mock_dates), \
         patch.object(nasa_service, 'fetch_apod', new_callable=AsyncMock, return_value=mock_apod):
        response = await client.get("/api/apod/list/cached")
        
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "results" in data
        assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_preload_apods(client):
    """Test preloading APODs endpoint."""
    with patch.object(nasa_service, 'preload_recent_apods', new_callable=AsyncMock) as mock_preload:
        response = await client.post("/api/apod/preload?days=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "preload started"
        assert data["days"] == 5


@pytest.mark.asyncio
async def test_preload_apods_invalid_days(client):
    """Test preloading with invalid days parameter."""
    # Test too few days
    response = await client.post("/api/apod/preload?days=0")
    assert response.status_code == 400
    
    # Test too many days
    response = await client.post("/api/apod/preload?days=400")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_apod_endpoint_error_handling(client):
    """Test error handling in APOD endpoint."""
    with patch.object(nasa_service, 'fetch_apod', new_callable=AsyncMock, side_effect=Exception("Test error")):
        response = await client.get("/api/apod/today")
        
        assert response.status_code == 500
        data = response.json()
        assert "Error fetching APOD" in data["detail"]
