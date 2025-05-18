import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "Book Management System"
    DEBUG: bool = True
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    OLLAMA_ENDPOINT: str = os.getenv("OLLAMA_ENDPOINT")
    AI_MODEL: str = os.getenv("LOCAL_AI_MODEL")
    OPEN_ROUTER_API_KEY: str = os.getenv("OPEN_ROUTER_API_KEY")
    USE_OPEN_ROUTER: bool = os.getenv("USE_OPEN_ROUTER", "False").lower() == "true"
    OPEN_ROUTER_MODEL: str = os.getenv("OPEN_ROUTER_MODEL")
    OPEN_ROUTER_URL: str = os.getenv("OPEN_ROUTER_URL")

settings = Settings()
