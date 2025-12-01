from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import List, Optional, Any
import json
from urllib.parse import quote


class Settings(BaseSettings):
    """Application settings."""
    
    # App Info
    APP_NAME: str = "Neusearch API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "A full-stack search application with RAG capabilities"
    ENVIRONMENT: str = "development"
    
    # API Settings
    API_PREFIX: str = "/api"
    DOCS_URL: Optional[str] = None  # Disable default Swagger UI
    REDOC_URL: Optional[str] = None  # Disable default ReDoc
    
    # CORS Settings - accept as strings, convert to lists after validation
    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"
    
    @model_validator(mode="after")
    def convert_cors_to_lists(self) -> "Settings":
        """Convert CORS string fields to lists after validation."""
        # Convert CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            if "," in self.CORS_ORIGINS:
                object.__setattr__(self, "CORS_ORIGINS", [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()])
            else:
                object.__setattr__(self, "CORS_ORIGINS", [self.CORS_ORIGINS.strip()] if self.CORS_ORIGINS.strip() else ["*"])
        
        # Convert CORS_ALLOW_METHODS
        if isinstance(self.CORS_ALLOW_METHODS, str):
            if "," in self.CORS_ALLOW_METHODS:
                object.__setattr__(self, "CORS_ALLOW_METHODS", [method.strip() for method in self.CORS_ALLOW_METHODS.split(",") if method.strip()])
            else:
                object.__setattr__(self, "CORS_ALLOW_METHODS", [self.CORS_ALLOW_METHODS.strip()] if self.CORS_ALLOW_METHODS.strip() else ["*"])
        
        # Convert CORS_ALLOW_HEADERS
        if isinstance(self.CORS_ALLOW_HEADERS, str):
            if "," in self.CORS_ALLOW_HEADERS:
                object.__setattr__(self, "CORS_ALLOW_HEADERS", [header.strip() for header in self.CORS_ALLOW_HEADERS.split(",") if header.strip()])
            else:
                object.__setattr__(self, "CORS_ALLOW_HEADERS", [self.CORS_ALLOW_HEADERS.strip()] if self.CORS_ALLOW_HEADERS.strip() else ["*"])
        
        # Build DATABASE_URL from individual credentials if DATABASE_URL is not provided
        if not self.DATABASE_URL and all([self.user, self.password, self.host, self.port, self.dbname]):
            # URL-encode username and password to handle special characters
            encoded_user = quote(self.user, safe='')
            encoded_password = quote(self.password, safe='')
            encoded_dbname = quote(self.dbname, safe='')
            # Construct DATABASE_URL from individual credentials
            object.__setattr__(self, "DATABASE_URL", f"postgresql://{encoded_user}:{encoded_password}@{self.host}:{self.port}/{encoded_dbname}")
        elif not self.DATABASE_URL:
            # Default to local development database
            object.__setattr__(self, "DATABASE_URL", "postgresql://neusearch:neusearch@localhost:5432/neusearch")
        
        # Build REDIS_URL from individual credentials if REDIS_URL is not provided
        if not self.REDIS_URL:
            if self.REDIS_PASSWORD:
                object.__setattr__(self, "REDIS_URL", f"redis://:{quote(self.REDIS_PASSWORD, safe='')}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}")
            else:
                object.__setattr__(self, "REDIS_URL", f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}")
        
        return self
    
    # Scalar Docs Settings
    SCALAR_THEME: str = "default"
    SCALAR_LAYOUT: str = "modern"
    SCALAR_SHOW_SIDEBAR: bool = True
    SCALAR_HIDE_DOWNLOAD_BUTTON: bool = False
    SCALAR_HIDE_MODELS: bool = False
    SCALAR_HIDE_SCHEMA: bool = False
    
    # Database Settings
    DATABASE_URL: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    host: Optional[str] = None
    port: Optional[str] = None
    dbname: Optional[str] = None
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # Redis Settings
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_DECODE_RESPONSES: bool = True
    
    # Scheduler Settings
    SCRAPE_INTERVAL_HOURS: int = 6
    
    # Startup Sync Settings
    SYNC_ON_STARTUP: bool = True  # Whether to sync products on app startup
    MIN_PRODUCTS_THRESHOLD: int = 10  # Minimum products to skip startup sync
    GENERATE_EMBEDDINGS_ON_STARTUP: bool = True  # Whether to generate embeddings for products without them on startup
    
    # Gemini API Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_EMBEDDING_DIMENSION: int = 1536  # 768, 1536, or 3072
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # Ignore extra fields in .env file
    )


settings = Settings()

