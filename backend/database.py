from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Configuration settings for the application, loaded from environment variables.
    """
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours

    class Config:
        # This tells pydantic-settings to load variables from a .env file
        env_file = ".env"

# Create an instance of the settings
settings = Settings()
