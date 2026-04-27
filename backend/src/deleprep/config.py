from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = "my_super_secret_key_development"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "postgresql://deleprep_user:deleprep_password@localhost/deleprep_db"
    test_user_email: str = "test@example.com"
    test_user_password: str = "password123"

    openai_api_key: str = "mock"
    openai_base_url: str = "http://localhost:8080/v1"
    openai_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"

settings = Settings()
