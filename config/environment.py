import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/PPG_DB")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", f"{FRONTEND_URL},http://localhost:3000,http://localhost:8080").split(",") if origin.strip()]
