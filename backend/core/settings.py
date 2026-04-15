from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    DEV_USER_ID: str = ""
    ALLOW_DEV_USER_FALLBACK: bool = False
    DEV_USER_EMAIL: str = ""

    # LLM
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_DB_URL: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
