from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = "my_super_secret_key_development"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "postgresql://deleprep_user:deleprep_password@localhost/deleprep_db"

    class Config:
        env_file = ".env"

settings = Settings()
