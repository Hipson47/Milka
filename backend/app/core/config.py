"""Configuration settings for the NanoBanana inpainting backend."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # NanoBanana API
    nanobanana_url: str = Field(
        default="https://api.nanobanana.ai/v1/inpaint",
        description="NanoBanana API endpoint URL"
    )
    nanobanana_key: str = Field(
        default="",
        description="NanoBanana API key"
    )
    
    # Request configuration
    request_timeout: int = Field(
        default=120,
        description="HTTP request timeout in seconds"
    )
    
    # Application settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # CORS settings
    allowed_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins"
    )
    
    # File upload limits
    max_file_size_mb: int = Field(
        default=10,
        description="Maximum file size in MB"
    )
    max_image_dimension: int = Field(
        default=2048,
        description="Maximum image width/height in pixels"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
