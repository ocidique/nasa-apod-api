# NASA APOD API

A dockerized FastAPI-based REST API service that fetches and caches NASA's Astronomy Picture of the Day (APOD). This service provides fast responses with caching, browsability features (next/previous), and follows RESTful API best practices.

## Features

- 🚀 **Fast API** built with FastAPI framework
- 🐳 **Dockerized** for easy deployment
- 💾 **Redis caching** for optimal performance
- 🔗 **RESTful design** with proper HTTP methods and status codes
- 🧭 **Browsability** with next/previous navigation links
- 📚 **Interactive documentation** with Swagger UI
- 🔄 **Background preloading** of APOD data
- 📅 **Date-based queries** to browse historical APODs

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- (Optional) NASA API key from [https://api.nasa.gov/](https://api.nasa.gov/)

### Running with Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/ocidique/nasa-apod-api.git
cd nasa-apod-api
```

2. (Optional) Create a `.env` file with your NASA API key:
```bash
cp .env.example .env
# Edit .env and add your NASA_API_KEY (or use DEMO_KEY)
```

3. Start the services:
```bash
docker-compose up -d
```

4. Access the API:
- API Documentation: http://localhost:8000
- Health Check: http://localhost:8000/health

### Running Locally (without Docker)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start Redis (required):
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install Redis locally
```

3. Create `.env` file:
```bash
cp .env.example .env
# Update REDIS_HOST=localhost if running Redis locally
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Get Today's APOD
```bash
GET /api/apod/today
```

### Get APOD by Date (Query Parameter)
```bash
GET /api/apod?date=2024-01-15
```

### Get APOD by Date (Path Parameter)
```bash
GET /api/apod/2024-01-15
```

### List Cached APODs
```bash
GET /api/apod/list/cached
```

### Preload APODs (Admin)
```bash
POST /api/apod/preload?days=30
```

### Health Check
```bash
GET /health
```

## API Response Format

Each APOD response includes:
- `date`: The date of the APOD
- `title`: Title of the picture
- `explanation`: Detailed description
- `url`: Direct URL to the image/video
- `media_type`: Type of media (image or video)
- `hdurl`: High-definition URL (when available)
- `copyright`: Copyright information (when applicable)
- `next_date`: URL to next APOD (for browsability)
- `prev_date`: URL to previous APOD (for browsability)

### Example Response
```json
{
  "date": "2024-01-15",
  "title": "Example APOD",
  "explanation": "Detailed explanation...",
  "url": "https://apod.nasa.gov/apod/image/2401/example.jpg",
  "media_type": "image",
  "hdurl": "https://apod.nasa.gov/apod/image/2401/example_hd.jpg",
  "copyright": "Photographer Name",
  "next_date": "/api/apod?date=2024-01-16",
  "prev_date": "/api/apod?date=2024-01-14"
}
```

## Configuration

Environment variables (`.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `NASA_API_KEY` | Your NASA API key | `DEMO_KEY` |
| `REDIS_HOST` | Redis server hostname | `redis` |
| `REDIS_PORT` | Redis server port | `6379` |
| `REDIS_DB` | Redis database number | `0` |
| `API_HOST` | API server host | `0.0.0.0` |
| `API_PORT` | API server port | `8000` |
| `USE_MOCK` | Use mock data for testing | `false` |
| `CACHE_TTL_RECENT` | Cache TTL for recent APODs in days (0=indefinite) | `0` |
| `CACHE_TTL_HISTORICAL` | Cache TTL for historical APODs in days | `365` |
| `CACHE_RECENT_DAYS_THRESHOLD` | Days to consider an APOD "recent" | `7` |

**Note**: When `USE_MOCK=true`, the API uses mock data instead of calling NASA's API. This is useful for:
- Testing in environments without internet access
- Development and testing without API rate limits
- Demonstrating the API functionality

**Cache Configuration**: The cache TTL settings allow you to tune the caching strategy. Since APOD data is immutable JSON (~1-2KB each), aggressive caching is recommended for better performance when browsing historical dates.

## Architecture

- **FastAPI**: Modern, fast web framework for building APIs
- **Redis**: In-memory cache for fast APOD retrieval
- **httpx**: Async HTTP client for NASA API calls
- **Pydantic**: Data validation and settings management
- **Docker**: Containerization for consistent deployment

## Caching Strategy

The API implements an intelligent caching strategy optimized for NASA APOD data:

**Why aggressive caching works:**
- APODs are **historical and immutable** - once published, they never change
- Data is **lightweight JSON** (~1-2KB per entry), not large image files
- Users often **browse historical dates** going back years

**Cache Duration:**
- **Recent APODs** (last 7 days): Cached **indefinitely** (no expiration)
  - Allows for occasional corrections or updates
  - Configurable via `CACHE_TTL_RECENT` (0 = indefinite)
- **Historical APODs** (older than 7 days): Cached for **1 year**
  - These are immutable and safe to cache long-term
  - Configurable via `CACHE_TTL_HISTORICAL` (default: 365 days)
  
**Additional Features:**
- Current day APOD: Auto-refreshed on startup
- Background preloading: Configurable via `/api/apod/preload` endpoint
- Configurable threshold: Adjust what's considered "recent" via `CACHE_RECENT_DAYS_THRESHOLD`

**Memory Efficiency:**
Even caching all ~11,000 historical APODs would only use ~11-22MB of Redis memory, making long-term caching practical and cost-effective.

## Development

### Project Structure
```
nasa-apod-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── models.py        # Pydantic models
│   ├── service.py       # NASA API service & caching
│   └── config.py        # Configuration settings
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

### Running Tests
```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests (if tests are added)
pytest
```

## API Best Practices

This API follows REST best practices:
- ✅ Proper HTTP status codes (200, 400, 500)
- ✅ Resource-based URLs
- ✅ JSON responses
- ✅ HATEOAS with navigation links (next/prev)
- ✅ Query parameters for filtering
- ✅ Health check endpoint
- ✅ API versioning (via /api prefix)
- ✅ Interactive documentation

## License

MIT

## Credits

Data provided by [NASA's APOD API](https://api.nasa.gov/)