import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "sem_checker"
    CHROME_BINARY: str = ""
    CHROME_PROFILE_ROOT: str = ""
    CHROME_PROFILE_CLONE_ROOT: str = "/home/nghia/.config/google-chrome-clone"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"
    CAPTURE_FULLPAGE: bool = True

    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SCREENSHOTS_DIR: str = os.path.join(BASE_DIR, "storage", "screenshots")
    HTML_DIR: str = os.path.join(BASE_DIR, "storage", "html")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
