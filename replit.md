# GovTracker2 - Discord Curator Management System

## Overview

GovTracker2 is a comprehensive Discord curator management system that has been migrated from Node.js + TypeScript to Python 3.12 + Flask. The system provides real-time monitoring of Discord servers, curator activity tracking, response time analytics, and automated task management with a modern iOS-style interface.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Python 3.12 + Flask with Blueprint-based modular architecture
- **Database ORM**: SQLAlchemy with dual database support (PostgreSQL for development, MySQL for production)
- **Task Scheduling**: APScheduler for background tasks and automated maintenance
- **Discord Integration**: discord.py for real-time server monitoring and bot functionality

### Frontend Architecture
- **UI Framework**: Static React build served by Flask
- **Styling**: Tailwind CSS with iOS-style design system
- **Charts**: Chart.js for data visualization
- **Theme System**: Dark/light mode with user preference persistence

### Database Design
The system uses MySQL-compatible schema design with:
- AUTO_INCREMENT primary keys instead of SERIAL
- VARCHAR columns for better MySQL compatibility
- DATETIME fields instead of TIMESTAMP
- JSON fields compatible with MySQL 5.7+

## Key Components

### 1. Discord Bot System
- **Real-time Monitoring**: Tracks messages, reactions, and responses across up to 8 Discord servers
- **Response Tracking**: Monitors curator response times to help requests using keywords like "куратор", "curator", "help", "помощь"
- **Activity Logging**: Records all curator activities with point-based scoring system
- **Notification System**: Sends role-based notifications for important events

### 2. Rating System
- **Point-based Scoring**: Messages (3 pts), Reactions (1 pt), Replies (2 pts), Task Verification (5 pts)
- **Rating Levels**: Excellent (50+), Good (35+), Normal (20+), Poor (10+), Terrible (0-9)
- **Response Time Bonuses**: Good responses (<60s) get bonuses, poor responses (>300s) get penalties

### 3. Management Modules
- **Curator Management**: CRUD operations with detailed statistics and activity tracking
- **Server Management**: Discord server configuration and monitoring setup
- **Task Reports**: Task completion tracking with approval workflow
- **Activity Monitoring**: Comprehensive activity logging with filtering and analytics

### 4. Backup System
- **Automated Backups**: Daily scheduled backups with configurable retention
- **Manual Backups**: On-demand backup creation with custom descriptions
- **Restore Functionality**: Database restoration from backup files

## Data Flow

### 1. Discord Event Processing
1. Discord bot receives events (messages, reactions, etc.)
2. Events are processed by MessageMonitor to determine relevance
3. Activities are logged to database with point calculations
4. Response tracking is updated for help requests
5. Real-time notifications are sent if configured

### 2. Rating Calculation
1. Hourly scheduler triggers rating updates
2. Recent activities (30 days) are analyzed per curator
3. Points are calculated based on activity types
4. Response time metrics are factored in
5. Final rating level is determined and stored

### 3. API Data Flow
1. Frontend makes REST API calls to Flask blueprints
2. Routes query SQLAlchemy models
3. Data is serialized to JSON using model to_dict() methods
4. Responses maintain exact compatibility with original Node.js API

## External Dependencies

### Python Packages
- **Flask**: Web framework and API server
- **SQLAlchemy**: Database ORM with MySQL/PostgreSQL support
- **discord.py**: Discord bot functionality
- **APScheduler**: Background task scheduling
- **PyMySQL**: MySQL database driver
- **psycopg2**: PostgreSQL database driver

### Frontend Dependencies
- **Tailwind CSS**: Utility-first CSS framework
- **Chart.js**: Data visualization library
- **Font Awesome**: Icon library

### Discord Integration
- **Bot Token**: Required environment variable for Discord API access
- **Server Permissions**: Bot needs message reading, reaction monitoring, and notification sending permissions

## Deployment Strategy

### Environment Configuration
The system supports flexible deployment through environment variables:
- `DATABASE_URL`: Switches between PostgreSQL (dev) and MySQL (prod)
- `DISCORD_TOKEN`: Discord bot authentication
- `BACKUP_PATH`: Backup file storage location
- `SESSION_SECRET`: Flask session security key

### Database Compatibility
The codebase is designed for seamless MySQL deployment:
- All models use MySQL-compatible field types
- JSON fields work with MySQL 5.7+
- Auto-increment IDs are properly configured
- Migration scripts handle PostgreSQL to MySQL conversion

### Production Deployment
1. Set environment variables for MySQL database
2. Install Python dependencies
3. Run database migrations
4. Start Flask application and Discord bot
5. Configure reverse proxy (nginx) for static file serving
6. Set up automated backup scheduling

### Development Setup
1. Use PostgreSQL for local development
2. Flask debug mode enabled
3. Hot reload for frontend development
4. Comprehensive logging for debugging

The system maintains full feature parity with the original Node.js version while providing enhanced performance through Python's robust ecosystem and improved maintainability through Flask's modular blueprint architecture.