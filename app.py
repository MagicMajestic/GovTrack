# GovTracker2 Python Migration by Replit Agent
import os
import logging
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from scheduler import init_scheduler

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "govtracker2-secret-key")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Import models to ensure tables are created
    from models import curator, activity, discord_server, response_tracking, task_report, user
    
    # Register blueprints
    from routes.dashboard import dashboard_bp
    from routes.curators import curators_bp
    from routes.activities import activities_bp
    from routes.servers import servers_bp
    from routes.task_reports import task_reports_bp
    from routes.settings import settings_bp
    from routes.backup import backup_bp
    
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(curators_bp, url_prefix='/api/curators')
    app.register_blueprint(activities_bp, url_prefix='/api/activities')
    app.register_blueprint(servers_bp, url_prefix='/api/servers')
    app.register_blueprint(task_reports_bp, url_prefix='/api/task-reports')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(backup_bp, url_prefix='/api/backup')
    
    # Main route to serve React app
    @app.route('/')
    @app.route('/<path:path>')
    def serve_react_app(path=''):
        return render_template('index.html')
    
    # Initialize scheduler
    init_scheduler(app)
    
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

# Initialize Discord bot in background
from discord_bot.bot import start_discord_bot
import threading

def run_discord_bot():
    start_discord_bot()

# Start Discord bot in separate thread
discord_thread = threading.Thread(target=run_discord_bot, daemon=True)
discord_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
