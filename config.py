from re import template
from pydantic import BaseSettings



class Settings(BaseSettings):
    app_name: str = "wudn API"
    secret_key: str
    upload_path: str = "/uploads"
    base_fe_url: str
    db_uri: str = "mongodb://mongo:27017"
    send_grid_key: str
    class Config:
        env_file = ".env"


settings = Settings()
