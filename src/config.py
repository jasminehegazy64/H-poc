"""Configuration management for the pipeline."""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Database
DATABASE_PATH = DATA_DIR / "market_intel.db"

# Ollama settings
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Pipeline settings
MAX_ARTICLES_PER_RUN = 200
DIGEST_TOP_N_PER_SECTOR = 5

# Topic categories
TOPICS = ["earnings", "ma", "regulatory", "macro", "other"]
SENTIMENTS = ["positive", "negative", "neutral"]

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
