from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    nasa_api_key: str = "DEMO_KEY"
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
