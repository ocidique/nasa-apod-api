"""Unit tests for Pydantic models."""
from app.models import APODResponse, APODListResponse


def test_apod_response_model():
    """Test APODResponse model with valid data."""
    data = {
        "date": "2024-01-15",
        "title": "Test APOD",
        "explanation": "Test explanation",
        "url": "https://example.com/image.jpg",
        "media_type": "image",
        "hdurl": "https://example.com/image_hd.jpg",
        "copyright": "Test Photographer",
        "next_date": "/api/apod?date=2024-01-16",
        "prev_date": "/api/apod?date=2024-01-14"
    }
    
    response = APODResponse(**data)
    
    assert response.date == "2024-01-15"
    assert response.title == "Test APOD"
    assert response.explanation == "Test explanation"
    assert response.url == "https://example.com/image.jpg"
    assert response.media_type == "image"
    assert response.hdurl == "https://example.com/image_hd.jpg"
    assert response.copyright == "Test Photographer"
    assert response.next_date == "/api/apod?date=2024-01-16"
    assert response.prev_date == "/api/apod?date=2024-01-14"


def test_apod_response_minimal_fields():
    """Test APODResponse with only required fields."""
    data = {
        "date": "2024-01-15",
        "title": "Test APOD",
        "explanation": "Test explanation",
        "url": "https://example.com/image.jpg",
        "media_type": "image",
    }
    
    response = APODResponse(**data)
    
    assert response.date == "2024-01-15"
    assert response.title == "Test APOD"
    assert response.hdurl is None
    assert response.copyright is None
    assert response.next_date is None
    assert response.prev_date is None


def test_apod_response_video_media_type():
    """Test APODResponse with video media type."""
    data = {
        "date": "2024-01-15",
        "title": "Video APOD",
        "explanation": "Video explanation",
        "url": "https://example.com/video.mp4",
        "media_type": "video",
    }
    
    response = APODResponse(**data)
    
    assert response.media_type == "video"
    assert response.url == "https://example.com/video.mp4"


def test_apod_list_response_model():
    """Test APODListResponse model."""
    apod1 = APODResponse(
        date="2024-01-15",
        title="APOD 1",
        explanation="Explanation 1",
        url="https://example.com/image1.jpg",
        media_type="image"
    )
    
    apod2 = APODResponse(
        date="2024-01-16",
        title="APOD 2",
        explanation="Explanation 2",
        url="https://example.com/image2.jpg",
        media_type="image"
    )
    
    list_response = APODListResponse(count=2, results=[apod1, apod2])
    
    assert list_response.count == 2
    assert len(list_response.results) == 2
    assert list_response.results[0].title == "APOD 1"
    assert list_response.results[1].title == "APOD 2"


def test_apod_list_response_empty():
    """Test APODListResponse with empty results."""
    list_response = APODListResponse(count=0, results=[])
    
    assert list_response.count == 0
    assert len(list_response.results) == 0
