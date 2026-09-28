"""
Bot Configuration and Environment Settings.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


@dataclass
class Config:
    """Application configuration."""
    bot_token: str = os.getenv("BOT_TOKEN", "")
    default_mode: str = os.getenv("DEFAULT_THEME_MODE", "dark")
    session_ttl_seconds: int = int(os.getenv("SESSION_TTL_SECONDS", "7200"))
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
