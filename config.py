# GovTracker2 Python Migration by Replit Agent
import os

class Config:
    # Database configuration with PostgreSQL/MySQL compatibility
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost/govtracker2')
    
    # Convert postgres:// to postgresql:// if needed
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Discord bot configuration
    DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN', 'your-discord-bot-token')
    
    # Application settings
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'govtracker2-secret-key')
    
    # Backup settings
    BACKUP_PATH = os.environ.get('BACKUP_PATH', './backups')
    
    # Rating system configuration
    RATING_POINTS = {
        'message': 3,
        'reaction': 1,
        'reply': 2,
        'task_verification': 5
    }
    
    RATING_LEVELS = {
        'excellent': 50,    # Великолепно
        'good': 35,         # Хорошо
        'normal': 20,       # Нормально
        'poor': 10,         # Плохо
        'terrible': 0       # Ужасно
    }
    
    # Response time thresholds (in seconds)
    RESPONSE_TIME_GOOD = 60
    RESPONSE_TIME_POOR = 300

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://localhost/govtracker2_dev')

class ProductionConfig(Config):
    DEBUG = False
    # MySQL configuration for production
    MYSQL_DATABASE_URI = os.environ.get('MYSQL_DATABASE_URL', 'mysql+pymysql://user:password@localhost/govtracker2')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
