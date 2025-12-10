import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '8b6f77032919654a2afbe29f4633be31'
    
    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'kush'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'inventory_db'
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Other configurations
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
