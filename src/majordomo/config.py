import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    qwen_api_key: str | None = os.getenv("QWEN_API_KEY") or None
    qwen_base_url: str = os.getenv(
        "QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    )
    chat_model: str = os.getenv("CHAT_MODEL", "qwen3.7-plus")
    judge_model: str = os.getenv("JUDGE_MODEL", "qwen3.7-max")
    embed_model: str = os.getenv("EMBED_MODEL", "text-embedding-v4")
    embed_dim: int = int(os.getenv("EMBED_DIM", "1024"))
    # "qwen" for the real platform, "mock" for deterministic offline dev/CI
    llm_backend: str = os.getenv("LLM_BACKEND", "mock")

    db_path: Path = field(
        default_factory=lambda: ROOT / os.getenv("MAJORDOMO_DB", "data/majordomo.db")
    )
    data_dir: Path = field(default_factory=lambda: ROOT / "data")


settings = Settings()
