import httpx
import redis.asyncio as redis
import json
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
from app.config import settings
from app.mock_data import MOCK_APOD_DATA


class NASAAPODService:
    """Service for fetching and caching NASA APOD data"""
    
    NASA_APOD_URL = "https://api.nasa.gov/planetary/apod"
    APOD_START_DATE = date(1995, 6, 16)  # First APOD date
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = await redis.from_url(
            f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
            encoding="utf-8",
            decode_responses=True
        )
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def fetch_apod(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Fetch APOD from NASA API or cache"""
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        
        # Try to get from cache first
        cached_data = await self._get_from_cache(date_str)
        if cached_data:
            return cached_data
        
        # Use mock data if configured
        if settings.use_mock:
            if date_str in MOCK_APOD_DATA:
                data = MOCK_APOD_DATA[date_str]
            else:
                # Generate a generic mock for any date
                data = {
                    "date": date_str,
                    "title": f"Mock APOD for {date_str}",
                    "explanation": "This is mock data used for testing when NASA API is unavailable.",
                    "url": f"https://apod.nasa.gov/apod/image/mock_{date_str}.jpg",
                    "media_type": "image",
                    "hdurl": f"https://apod.nasa.gov/apod/image/mock_{date_str}_hd.jpg"
                }
        else:
            # Fetch from NASA API
            async with httpx.AsyncClient() as client:
                params = {
                    "api_key": settings.nasa_api_key,
                    "date": date_str
                }
                response = await client.get(self.NASA_APOD_URL, params=params)
                response.raise_for_status()
                data = response.json()
        
        # Store in cache
        await self._store_in_cache(date_str, data)
        
        return data
    
    async def _get_from_cache(self, date_str: str) -> Optional[Dict[str, Any]]:
        """Get APOD from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            cached = await self.redis_client.get(f"apod:{date_str}")
            if cached:
                return json.loads(cached)
        except Exception:
            pass
        
        return None
    
    async def _store_in_cache(self, date_str: str, data: Dict[str, Any]):
        """Store APOD in Redis cache with intelligent TTL strategy
        
        Since APOD data is historical and immutable (only JSON, no large files),
        we can cache it for extended periods:
        - Recent APODs (last week): Cache indefinitely (may have corrections)
        - Historical APODs (older): Cache for 1 year
        """
        if not self.redis_client:
            return
        
        try:
            target_date = datetime.fromisoformat(date_str).date()
            days_ago = (date.today() - target_date).days
            
            # Determine cache TTL based on age
            if days_ago <= settings.cache_recent_days_threshold:
                # Recent APODs: cache indefinitely (no expiration)
                # These might occasionally get corrections/updates
                if settings.cache_ttl_recent == 0:
                    await self.redis_client.set(f"apod:{date_str}", json.dumps(data))
                else:
                    await self.redis_client.setex(
                        f"apod:{date_str}",
                        timedelta(days=settings.cache_ttl_recent),
                        json.dumps(data)
                    )
            else:
                # Historical APODs: cache for long period (default 1 year)
                # These are immutable and only consume minimal space (JSON only)
                await self.redis_client.setex(
                    f"apod:{date_str}",
                    timedelta(days=settings.cache_ttl_historical),
                    json.dumps(data)
                )
        except Exception:
            pass
    
    async def get_available_dates(self) -> list[str]:
        """Get list of dates that have been cached"""
        if not self.redis_client:
            return []
        
        try:
            # Use SCAN instead of KEYS for non-blocking iteration
            dates = []
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor, 
                    match="apod:*",
                    count=100
                )
                dates.extend([key.split(":")[1] for key in keys])
                if cursor == 0:
                    break
            return sorted(dates, reverse=True)
        except Exception:
            return []
    
    async def preload_recent_apods(self, days: int = 30):
        """Preload recent APODs into cache"""
        today = date.today()
        for i in range(days):
            target_date = today - timedelta(days=i)
            if target_date >= self.APOD_START_DATE:
                try:
                    await self.fetch_apod(target_date)
                except Exception:
                    # Skip dates that don't have APOD (e.g., future dates or missing dates)
                    continue
    
    def get_next_date(self, current_date: date) -> Optional[date]:
        """Get the next date that could have an APOD"""
        next_date = current_date + timedelta(days=1)
        today = date.today()
        
        if next_date > today:
            return None
        
        return next_date
    
    def get_prev_date(self, current_date: date) -> Optional[date]:
        """Get the previous date that could have an APOD"""
        prev_date = current_date - timedelta(days=1)
        
        if prev_date < self.APOD_START_DATE:
            return None
        
        return prev_date


# Global service instance
nasa_service = NASAAPODService()
