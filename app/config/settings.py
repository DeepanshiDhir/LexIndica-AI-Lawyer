import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Fix macOS duplicate libomp initialization between PyTorch and FAISS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    INDEX_DIR: Path = DATA_DIR / "indexes"

    # API Keys
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Models
    MAIN_LLM_MODEL: str = "gemini-flash-lite-latest"
    LIGHTWEIGHT_LLM_MODEL: str = "gemini-flash-lite-latest"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DEVICE: str = "cpu"
    DOWNLOAD_HF_EMBEDDINGS: bool = False  # Set to true if you want to download the 2.2GB HuggingFace model
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    USE_CROSS_ENCODER: bool = False

    # Retrieval parameters
    DENSE_TOP_K: int = 15
    SPARSE_TOP_K: int = 15
    RRF_K: int = 60
    FINAL_TOP_K: int = 5
    RELEVANCE_THRESHOLD: float = 0.50

    # Safety and loops
    ENABLE_INJECTION_DEFENSE: bool = True
    MAX_AGENT_CORRECTIONS: int = 2

    # App environment
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"


settings = Settings()
