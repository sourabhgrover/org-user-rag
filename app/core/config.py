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

     # Add JWT Secret Key
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-that-should-be-randomly-generated-in-prod-5b3f7e9a2c1d")
    # For production, replace the default with a robust generation or environment variable
    # Example for generating: import secrets; secrets.token_hex(32)

    #OPENAI API Key
    OPENAI_API_KEY: str

    
    
    # Pinecone settings
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME: str = "org-documents"

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

# Create settings instance
settings = Settings()