from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Loads and validates environment variables from the .env file."""
    GEMINI_API_KEY: str = "your_google_ai_studio_gemini_api_key_here"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = AppSettings()
