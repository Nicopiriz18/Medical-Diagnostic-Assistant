from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    LLM_BASE_URL: str = "https://api.openai.com"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4.1-mini"  # poné el que uses
    APP_ENV: str = "dev"

settings = Settings()