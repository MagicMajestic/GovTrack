# GovTracker2 Python Migration by Replit Agent
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine, text
import os

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def init_db(app):
    """Initialize database with the Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we're using MySQL and set appropriate SQL mode
        if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI']:
            try:
                db.session.execute(text("SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'"))
                db.session.commit()
            except Exception as e:
                print(f"Warning: Could not set MySQL SQL mode: {e}")

def get_database_type():
    """Determine if we're using PostgreSQL or MySQL"""
    database_url = os.environ.get('DATABASE_URL', '')
    if 'mysql' in database_url:
        return 'mysql'
    return 'postgresql'

def create_mysql_compatible_engine(database_url):
    """Create SQLAlchemy engine with MySQL compatibility settings"""
    if 'mysql' in database_url:
        # MySQL specific engine options
        engine = create_engine(
            database_url,
            pool_recycle=300,
            pool_pre_ping=True,
            connect_args={
                "charset": "utf8mb4",
                "sql_mode": "STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"
            }
        )
    else:
        # PostgreSQL engine
        engine = create_engine(
            database_url,
            pool_recycle=300,
            pool_pre_ping=True
        )
    
    return engine
