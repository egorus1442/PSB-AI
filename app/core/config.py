import os

class Settings:
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key_here")

    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

settings = Settings()