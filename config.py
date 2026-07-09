# config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # MySQL Database connection settings
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    DB_NAME = 'career_compass_db'