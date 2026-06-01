import os

class Settings:
    PROJECT_NAME: str = "Aegis-Tetris Analyzer API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS Origins allowed
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",  # Frontend dashboard
        "http://127.0.0.1:3000",
        "chrome-extension://*",   # Allow Chrome extensions
        "*"                       # Open for other connections in development
    ]

settings = Settings()
