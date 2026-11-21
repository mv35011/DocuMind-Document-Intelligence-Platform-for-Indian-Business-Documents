import os
from functools import lru_cache
from typing import Literal

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

        ENVIRONMENT: str = "development"
        DEBUG: bool = True

        DATABASE_URL: str = "postgresql+asyncpg://documind:documind@localhost:5432/documind"
        DATABASE_READONLY_URL: str = "postgresql+asyncpg://documind_readonly:readonly_pass@localhost:5432/documind"
        REDIS_URL: str = "redis://localhost:6379/0"

        S3_ENDPOINT_URL: str = "http://localhost:9000"
        S3_BUCKET: str = "documind-documents"
        AWS_ACCESS_KEY_ID: str = "minioadmin"
        AWS_SECRET_ACCESS_KEY: str = "minioadmin"
        AWS_REGION: str = "ap-south-1"

        QDRANT_URL: str = "http://localhost:6333"
        MLFLOW_TRACKING_URI: str = "http://localhost:5001"

        JWT_SECRET: str = "documind-local-dev-jwt-secret-key-32bytes-min"
        JWT_ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

        EXTRACTOR_BACKEND: Literal["stub", "regex", "ocr_llm", "vlm_prompted", "vlm_finetuned"] = "stub"
        OCR_ENGINE: Literal["tesseract", "paddle"] = "tesseract"
        AUTO_APPROVE_THRESHOLD: float = 0.88
        MAX_UPLOAD_MB: int = 20
        MAX_PAGES: int = 20

        LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
        LLM_API_KEY: str = "gsk_test"
        LLM_MODEL: str = "llama-3.3-70b-versatile"
        VLM_BASE_URL: str = "http://localhost:8000/v1"
        VLM_MODEL: str = "Qwen/Qwen2-VL-2B-Instruct"

except ImportError:
    class Settings:  # type: ignore[no-redef]
        def __init__(self) -> None:
            self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
            self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"
            self.DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://documind:documind@localhost:5432/documind")
            self.DATABASE_READONLY_URL = os.getenv("DATABASE_READONLY_URL", "postgresql+asyncpg://documind_readonly:readonly_pass@localhost:5432/documind")
            self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
            self.S3_BUCKET = os.getenv("S3_BUCKET", "documind-documents")
            self.AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
            self.AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
            self.AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
            self.QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
            self.MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
            self.JWT_SECRET = os.getenv("JWT_SECRET", "documind-local-dev-jwt-secret-key-32bytes-min")
            self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
            self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
            self.EXTRACTOR_BACKEND = os.getenv("EXTRACTOR_BACKEND", "stub")
            self.OCR_ENGINE = os.getenv("OCR_ENGINE", "tesseract")
            self.AUTO_APPROVE_THRESHOLD = float(os.getenv("AUTO_APPROVE_THRESHOLD", "0.88"))
            self.MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))
            self.MAX_PAGES = int(os.getenv("MAX_PAGES", "20"))
            self.LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
            self.LLM_API_KEY = os.getenv("LLM_API_KEY", "gsk_test")
            self.LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
            self.VLM_BASE_URL = os.getenv("VLM_BASE_URL", "http://localhost:8000/v1")
            self.VLM_MODEL = os.getenv("VLM_MODEL", "Qwen/Qwen2-VL-2B-Instruct")


@lru_cache
def get_settings() -> Settings:
    return Settings()
