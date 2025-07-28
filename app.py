import os
import logging
from flask import Flask, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "govtracker2-secret-key")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 'postgresql://localhost/govtracker2')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize database
    db.init_app(app)
    
    # Import models to ensure tables are created
    try:
        from models import curator, activity, discord_server, response_tracking, task_report, user
    except ImportError as e:
        logging.warning(f"Could not import models: {e}")
    
    # Register blueprints (with error handling for missing routes)
    try:
        from routes.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    except ImportError:
        logging.warning("Dashboard blueprint not found")
        
    try:
        from routes.curators import curators_bp
        app.register_blueprint(curators_bp, url_prefix='/api/curators')
    except ImportError:
        logging.warning("Curators blueprint not found")
        
    try:
        from routes.activities import activities_bp
        app.register_blueprint(activities_bp, url_prefix='/api/activities')
    except ImportError:
        logging.warning("Activities blueprint not found")
        
    try:
        from routes.servers import servers_bp
        app.register_blueprint(servers_bp, url_prefix='/api/servers')
    except ImportError:
        logging.warning("Servers blueprint not found")
        
    try:
        from routes.task_reports import task_reports_bp
        app.register_blueprint(task_reports_bp, url_prefix='/api/task-reports')
    except ImportError:
        logging.warning("Task reports blueprint not found")
        
    try:
        from routes.settings import settings_bp
        app.register_blueprint(settings_bp, url_prefix='/api/settings')
    except ImportError:
        logging.warning("Settings blueprint not found")
        
    try:
        from routes.backup import backup_bp
        app.register_blueprint(backup_bp, url_prefix='/api/backup')
    except ImportError:
        logging.warning("Backup blueprint not found")
    
    # Static file serving
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory('static', filename)
    
    # Main route to serve React app
    @app.route('/')
    @app.route('/<path:path>')
    def serve_react_app(path=''):
        try:
            return render_template('index.html')
        except:
            return send_from_directory('static', 'index.html')
    
    # Initialize scheduler (with error handling)
    try:
        from scheduler import init_scheduler
        init_scheduler(app)
    except ImportError:
        logging.warning("Scheduler not available")
    
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

# Initialize Discord bot in background (with error handling)
try:
    discord_token = os.environ.get('DISCORD_TOKEN')
    if discord_token and discord_token != 'your-discord-bot-token':
        from discord_bot.bot import start_discord_bot
        import threading

        def run_discord_bot():
            try:
                start_discord_bot()
            except Exception as e:
                logging.error(f"Discord bot failed to start: {e}")

        # Start Discord bot in separate thread
        discord_thread = threading.Thread(target=run_discord_bot, daemon=True)
        discord_thread.start()
        logging.info("Discord bot thread started")
    else:
        logging.info("Discord bot not started - no token provided")
except Exception as e:
    logging.warning(f"Could not initialize Discord bot: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
