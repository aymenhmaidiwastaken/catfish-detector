from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERP_API_KEY: str | None = None
    SERPER_API_KEY: str | None = None  # serper.dev - 2500 free searches/month
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    TEMP_DIR: str = "./tmp_uploads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
