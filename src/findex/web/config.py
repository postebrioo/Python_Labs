from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    index_path: str = "index.pkl"
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()