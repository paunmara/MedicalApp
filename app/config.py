from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    #secret key for sign - in sessions
    SECRET_KEY: str = 'secret-key-change-this'

    #SQLite database URL
    DATABASE_URL: str = 'sqlite:///./MedicalApp'

    class Config:
        env_file = ".env"

settings = Settings()














