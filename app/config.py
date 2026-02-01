from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    nasa_api_key: str = "DEMO_KEY"
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    use_mock: bool = False  # Use mock data instead of NASA API (for testing)
    max_cached_list_size: int = 50  # Maximum number of APODs to return in list endpoint
    
    # Caching strategy settings (in days)
    # APODs are historical and immutable, so we can cache them for long periods
    cache_ttl_recent: int = 0  # Recent APODs (last week): no expiration (0 = indefinite)
    cache_ttl_historical: int = 365  # Historical APODs (older than 1 week): 1 year
    cache_recent_days_threshold: int = 7  # Days to consider an APOD "recent"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
