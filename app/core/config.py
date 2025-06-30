import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Org User RAG API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database settings for MongoDB - NOW REQUIRED!
    MONGO_URI: str  # No default value, so it's required
    MONGO_DB_NAME: str
    
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

# Create settings instance
settings = Settings()