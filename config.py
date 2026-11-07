import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).with_name(".env"), override=False)


class Config:
    DOBBY_API_URL = os.getenv("DOBBY_API_URL", "https://dobby-api-system.onrender.com")
    DOBBY_API_CONNECT_TIMEOUT = float(os.getenv("DOBBY_API_CONNECT_TIMEOUT", "5"))
    DOBBY_API_READ_TIMEOUT = float(os.getenv("DOBBY_API_READ_TIMEOUT", "45"))
    DOBBY_CACHE_TTL = int(os.getenv("DOBBY_CACHE_TTL", "30"))
    DOBBY_API_RETRIES = int(os.getenv("DOBBY_API_RETRIES", "1"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
