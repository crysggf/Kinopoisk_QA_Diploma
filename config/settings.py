import os

from dotenv import load_dotenv

load_dotenv()

BASE_URL: str = os.getenv(
    "BASE_URL",
    "https://api.kinopoisk.dev/v1.4",
)
API_TOKEN: str = os.getenv("API_TOKEN", "")
