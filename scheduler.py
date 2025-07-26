# GovTracker2 Python Migration by Replit Agent
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.backup_service import create_automatic_backup
import logging
import atexit

scheduler = None

def init_scheduler(app):
    """Initialize APScheduler for background tasks"""
    global scheduler
    
    scheduler = BackgroundScheduler()
    
    # Schedule automatic backup every day at 2 AM
    scheduler.add_job(
        func=create_automatic_backup,
        trigger=CronTrigger(hour=2, minute=0),
        id='daily_backup',
        name='Daily automatic backup',
        replace_existing=True
    )
    
    # Schedule rating calculations every hour
    scheduler.add_job(
        func=update_curator_ratings,
        trigger=CronTrigger(minute=0),
        id='hourly_rating_update',
        name='Hourly rating update',
        replace_existing=True
    )
    
    scheduler.start()
    logging.info("APScheduler started successfully")
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

def update_curator_ratings():
    """Update curator ratings based on recent activities"""
    from app import app, db
    from models.curator import Curator
    from utils.rating import calculate_curator_rating
    
    with app.app_context():
        try:
            curators = Curator.query.all()
            for curator in curators:
                rating_data = calculate_curator_rating(curator.id)
                curator.total_points = rating_data['total_points']
                curator.rating_level = rating_data['level']
            
            db.session.commit()
            logging.info(f"Updated ratings for {len(curators)} curators")
        except Exception as e:
            logging.error(f"Error updating curator ratings: {e}")
            db.session.rollback()

def get_scheduler():
    """Get the global scheduler instance"""
    return scheduler
