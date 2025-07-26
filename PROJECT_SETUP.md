# GovTracker2 - Setup Instructions

## Project Overview
GovTracker2 is a comprehensive Discord curator management system migrated from Node.js + TypeScript to Python 3.12 + Flask. The system provides real-time monitoring of Discord servers, curator activity tracking, response time analytics, and automated task management with a modern iOS-style interface.

## Author Attribution
**Migrated by**: Replit Agent  
**Original Project**: GovTracker2 Node.js/TypeScript system  
**Migration Date**: January 2025  
**Python Version**: 3.12  
**Framework**: Flask with Blueprint architecture

## Prerequisites
- Python 3.12 or higher
- PostgreSQL (for development) or MySQL (for production)
- Discord Bot Token (for Discord integration)
- Node.js (for frontend development tools - optional)

## Installation Instructions

### 1. Environment Setup
```bash
# Install Python dependencies (automatically handled in Replit)
# Dependencies: flask, sqlalchemy, discord.py, apscheduler, psycopg2-binary, pymysql

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/govtracker2"
export DISCORD_TOKEN="your_discord_bot_token"
export SESSION_SECRET="your_session_secret_key"
```

### 2. Database Setup
```bash
# PostgreSQL (Development)
createdb govtracker2

# MySQL (Production)
mysql -u root -p -e "CREATE DATABASE govtracker2;"
```

### 3. Application Configuration
The system automatically detects database type from DATABASE_URL:
- PostgreSQL: `postgresql://...` 
- MySQL: `mysql://...`

### 4. Discord Bot Setup
1. Create Discord Application at https://discord.com/developers/applications
2. Create Bot and copy token
3. Add bot to servers with permissions:
   - Read Messages
   - Send Messages
   - Add Reactions
   - Manage Messages
   - View Channels

### 5. Running the Application
```bash
# Start the application
gunicorn --bind 0.0.0.0:5000 --reload main:app

# Or for development
python main.py
```

## Project Structure

```
govtracker2/
├── app.py                 # Flask application factory
├── main.py               # Application entry point
├── config.py             # Configuration settings
├── database.py           # Database utilities
├── scheduler.py          # Background task scheduler
├── models/               # SQLAlchemy models
│   ├── curator.py        # Curator data model
│   ├── activity.py       # Activity tracking model
│   ├── discord_server.py # Discord server model
│   ├── response_tracking.py # Response time tracking
│   ├── task_report.py    # Task report model
│   └── user.py          # User management model
├── routes/               # Flask blueprints
│   ├── dashboard.py      # Dashboard API endpoints
│   ├── curators.py       # Curator management
│   ├── activities.py     # Activity tracking
│   ├── servers.py        # Server management
│   ├── task_reports.py   # Task report management
│   ├── settings.py       # System settings
│   └── backup.py         # Backup management
├── discord_bot/          # Discord bot functionality
│   ├── bot.py           # Main bot instance
│   ├── monitoring.py    # Message monitoring
│   └── notifications.py # Notification system
├── utils/                # Utility functions
│   ├── rating.py        # Rating calculation
│   ├── response_time.py # Response time analysis
│   └── backup_service.py # Backup operations
├── static/               # Frontend assets
│   ├── js/              # JavaScript modules
│   │   ├── app.js       # Main application
│   │   ├── curators.js  # Curator management
│   │   ├── activities.js # Activity tracking
│   │   ├── servers.js   # Server management
│   │   ├── reports.js   # Task reports
│   │   ├── settings.js  # Settings management
│   │   └── backup.js    # Backup management
│   └── css/             # Stylesheets (if any)
└── templates/            # HTML templates
    └── index.html       # Single-page application
```

## Key Features

### 1. Curator Management
- Add/edit/delete curators
- Track performance metrics
- Rating system with 5 levels (Excellent to Terrible)
- Faction and subdivision management

### 2. Activity Tracking
- Real-time Discord message monitoring
- Point-based scoring system
- Response time tracking
- Activity type categorization

### 3. Server Management
- Monitor up to 8 Discord servers
- Server configuration management
- Activity statistics per server

### 4. Task Reports
- Task completion tracking
- Approval workflow
- Completion rate calculations
- Report management

### 5. Backup System
- Automated daily backups
- Manual backup creation
- Restore functionality
- Backup cleanup and management

### 6. Settings Management
- Discord bot configuration
- Rating system parameters
- Notification settings
- System preferences

## Database Schema

### Primary Tables
- `curators` - Curator information and statistics
- `activities` - Activity tracking records
- `discord_servers` - Monitored Discord servers
- `response_tracking` - Response time metrics
- `task_reports` - Task completion reports
- `users` - System user management

### Key Relationships
- Curators have many Activities
- Activities belong to Curators and Servers
- Response tracking links to Activities
- Task reports belong to Curators

## API Endpoints

### Dashboard
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/dashboard/activity-summary` - Activity summary

### Curators
- `GET /api/curators` - List all curators
- `POST /api/curators` - Create curator
- `PUT /api/curators/{id}` - Update curator
- `DELETE /api/curators/{id}` - Delete curator

### Activities
- `GET /api/activities` - List activities
- `POST /api/activities` - Log activity
- `GET /api/activities/daily` - Daily statistics

### Servers
- `GET /api/servers` - List servers
- `POST /api/servers` - Add server
- `PUT /api/servers/{id}` - Update server
- `DELETE /api/servers/{id}` - Remove server

### Task Reports
- `GET /api/task-reports` - List reports
- `POST /api/task-reports` - Create report
- `PUT /api/task-reports/{id}` - Update report
- `DELETE /api/task-reports/{id}` - Delete report

### Settings
- `GET /api/settings` - Get settings
- `PUT /api/settings/bot` - Update bot settings
- `PUT /api/settings/rating` - Update rating settings

### Backup
- `GET /api/backup` - List backups
- `POST /api/backup/create` - Create backup
- `POST /api/backup/restore/{filename}` - Restore backup
- `DELETE /api/backup/delete/{filename}` - Delete backup

## Frontend Features

### Modern UI
- iOS-style interface design
- Dark/light mode toggle
- Responsive layout
- Real-time updates

### Interactive Components
- Modal dialogs for data entry
- Toast notifications
- Loading states
- Error handling

### Data Visualization
- Chart.js integration
- Activity charts
- Rating distribution
- Performance metrics

## Production Deployment

### Environment Variables
```
DATABASE_URL=mysql://user:password@host:3306/govtracker2
DISCORD_TOKEN=your_discord_bot_token
SESSION_SECRET=your_secure_session_key
BACKUP_PATH=/path/to/backup/directory
```

### MySQL Configuration
The system is designed for seamless MySQL deployment:
- AUTO_INCREMENT primary keys
- VARCHAR columns for better compatibility
- DATETIME fields instead of TIMESTAMP
- JSON fields compatible with MySQL 5.7+

### Performance Optimization
- Connection pooling enabled
- Query optimization
- Cached statistics
- Background task scheduling

## Troubleshooting

### Common Issues
1. **Database Connection**: Verify DATABASE_URL format
2. **Discord Bot**: Ensure DISCORD_TOKEN is set and valid
3. **Permissions**: Check bot permissions in Discord servers
4. **Dependencies**: Ensure all Python packages are installed

### Logging
The application provides comprehensive logging:
- Database operations
- Discord bot events
- API requests
- Error tracking

## Support and Maintenance

### Regular Tasks
- Monitor backup creation
- Check Discord bot status
- Review activity data
- Update curator ratings

### Database Maintenance
- Regular backup verification
- Performance monitoring
- Index optimization
- Data cleanup

## Migration Notes

This project was successfully migrated from Node.js/TypeScript to Python 3.12/Flask while maintaining:
- Complete feature parity
- Data structure compatibility
- API endpoint compatibility
- Frontend functionality

The migration provides enhanced performance through Python's robust ecosystem and improved maintainability through Flask's modular blueprint architecture.