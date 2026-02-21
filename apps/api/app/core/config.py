from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Legacy LLM Config (backward compatibility)
    LLM_BASE_URL: str = "https://api.openai.com"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4-turbo"

    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL_TEXT: str = "gpt-4-turbo"
    OPENAI_MODEL_VISION: str = "gpt-4o"

    # PostgreSQL Configuration
    DATABASE_URL: str = "postgresql+asyncpg://medassist_user:medassist_dev_password@postgres:5432/medassist"

    # Storage Configuration
    LOCAL_STORAGE_PATH: str = "./uploads"
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # Agent Configuration
    MAX_INTERVIEW_TURNS: int = 20
    CONFIDENCE_THRESHOLD: float = 0.7

    # Application Environment
    APP_ENV: str = "dev"

    @property
    def use_s3(self) -> bool:
        """Check if S3 storage should be used"""
        return bool(self.S3_BUCKET and self.AWS_ACCESS_KEY_ID)

settings = Settings()