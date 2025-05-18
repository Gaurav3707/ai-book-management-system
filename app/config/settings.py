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
    USE_LOCAL_MODEL: bool = os.getenv("USE_LOCAL_MODEL", "False").lower() == "true"
    LOCALLY_DEPLOYED_LLM_ENDPOINT: str = os.getenv("LOCALLY_DEPLOYED_LLM_ENDPOINT")
    LOCAL_AI_MODEL: str = os.getenv("LOCAL_AI_MODEL")
    HOSTED_MODEL_API_KEY: str = os.getenv("HOSTED_MODEL_API_KEY")
    HOSTED_MODEL_MODEL: str = os.getenv("HOSTED_MODEL_MODEL")
    HOSTED_MODEL_ENDPOINT: str = os.getenv("HOSTED_MODEL_ENDPOINT")

settings = Settings()
