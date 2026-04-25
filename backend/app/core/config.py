"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object.

    Values are loaded (in order of precedence) from:
    1. Environment variables.
    2. A ``.env`` file in the repo root.
    3. Defaults defined here.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Core ---------------------------------------------------------------
    app_env: Literal["development", "staging", "production", "test"] = "development"
    app_name: str = "vision-sop"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_secret_key: str = "dev-insecure-change-me"
    app_log_level: str = "INFO"
    app_role: Literal["api", "worker"] = "api"

    # --- Database -----------------------------------------------------------
    database_url: str = "postgresql+psycopg://vision:vision@localhost:5432/vision_sop"
    database_pool_size: int = 10

    # --- Redis --------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"

    # --- LLM ----------------------------------------------------------------
    llm_provider: Literal["openai", "anthropic", "ollama", "stub"] = "stub"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # --- Vision -------------------------------------------------------------
    yolo_model: str = "yolov8n-pose.pt"
    yolo_detect_model: str = "yolov8n.pt"
    yolo_conf_threshold: float = 0.4
    pipeline_target_fps: int = 10
    pipeline_max_workers: int = 2

    # --- Privacy ------------------------------------------------------------
    privacy_face_blur: bool = True
    privacy_store_raw_clips: bool = False
    privacy_retention_days: int = 30

    # --- Paths --------------------------------------------------------------
    data_dir: Path = Path("/app/data")
    video_dir: Path = Path("/app/data/videos")
    model_dir: Path = Path("/app/data/models")
    sop_dir: Path = Path("/app/data/generated_sops")
    heatmap_dir: Path = Path("/app/data/heatmaps")

    # --- JWT ----------------------------------------------------------------
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24  # one day

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def ensure_dirs(self) -> None:
        """Create data directories if they don't exist."""
        for p in (self.data_dir, self.video_dir, self.model_dir, self.sop_dir, self.heatmap_dir):
            p.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    s = Settings()
    # Be forgiving in dev: don't crash if dirs aren't writable (e.g. tests).
    try:
        s.ensure_dirs()
    except OSError:
        pass
    return s


settings = get_settings()
