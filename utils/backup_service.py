# GovTracker2 Python Migration by Replit Agent
import os
import json
import uuid
import gzip
from datetime import datetime
from database import db
from models.curator import Curator
from models.activity import Activity
from models.discord_server import DiscordServer
from models.response_tracking import ResponseTracking
from models.task_report import TaskReport
from models.user import User
import logging

def create_backup(name=None, description="Manual backup", include_files=False):
    """Create a backup of the database"""
    try:
        backup_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Create backup directory if it doesn't exist
        backup_path = os.environ.get('BACKUP_PATH', './backups')
        os.makedirs(backup_path, exist_ok=True)
        
        # Collect data from all tables
        backup_data = {
            'metadata': {
                'id': backup_id,
                'name': name or f"backup_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                'description': description,
                'created_at': timestamp.isoformat(),
                'version': '1.0',
                'source': 'GovTracker2 Python Migration',
                'include_files': include_files
            },
            'data': {}
        }
        
        # Backup curators
        curators = Curator.query.all()
        backup_data['data']['curators'] = [curator.to_dict() for curator in curators]
        
        # Backup discord servers
        servers = DiscordServer.query.all()
        backup_data['data']['discord_servers'] = [server.to_dict() for server in servers]
        
        # Backup activities
        activities = Activity.query.all()
        backup_data['data']['activities'] = [activity.to_dict() for activity in activities]
        
        # Backup response tracking
        responses = ResponseTracking.query.all()
        backup_data['data']['response_tracking'] = [response.to_dict() for response in responses]
        
        # Backup task reports
        task_reports = TaskReport.query.all()
        backup_data['data']['task_reports'] = [report.to_dict() for report in task_reports]
        
        # Backup users (excluding sensitive data)
        users = User.query.all()
        backup_data['data']['users'] = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
            for user in users
        ]
        
        # Calculate statistics
        stats = {
            'tables_count': len(backup_data['data']),
            'curators_count': len(backup_data['data']['curators']),
            'servers_count': len(backup_data['data']['discord_servers']),
            'activities_count': len(backup_data['data']['activities']),
            'responses_count': len(backup_data['data']['response_tracking']),
            'reports_count': len(backup_data['data']['task_reports']),
            'users_count': len(backup_data['data']['users'])
        }
        
        backup_data['metadata']['statistics'] = stats
        
        # Save backup file
        backup_filename = f"{backup_id}.json"
        backup_file_path = os.path.join(backup_path, backup_filename)
        
        # Compress the backup for smaller file size
        with gzip.open(backup_file_path + '.gz', 'wt', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        # Get file size
        file_size = os.path.getsize(backup_file_path + '.gz')
        
        backup_info = {
            'id': backup_id,
            'name': backup_data['metadata']['name'],
            'description': description,
            'created_at': timestamp.isoformat(),
            'file_path': backup_file_path + '.gz',
            'size': file_size,
            'statistics': stats
        }
        
        logging.info(f"Backup created successfully: {backup_id}")
        
        return {
            'success': True,
            'backup_info': backup_info
        }
        
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def restore_from_backup(backup_id, force=False, is_file_path=False):
    """Restore database from backup"""
    try:
        if is_file_path:
            # backup_id is actually a file path
            backup_file_path = backup_id
        else:
            backup_path = os.environ.get('BACKUP_PATH', './backups')
            backup_file_path = os.path.join(backup_path, f"{backup_id}.json.gz")
        
        if not os.path.exists(backup_file_path):
            return {
                'success': False,
                'error': 'Backup file not found'
            }
        
        # Read backup data
        if backup_file_path.endswith('.gz'):
            with gzip.open(backup_file_path, 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)
        else:
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
        
        # Validate backup format
        if 'metadata' not in backup_data or 'data' not in backup_data:
            return {
                'success': False,
                'error': 'Invalid backup format'
            }
        
        # Check if database has data and force flag
        existing_curators = Curator.query.count()
        if existing_curators > 0 and not force:
            return {
                'success': False,
                'error': 'Database contains data. Use force=True to overwrite.'
            }
        
        restored_tables = []
        statistics = {}
        
        # Clear existing data if force restore
        if force:
            logging.info("Force restore: clearing existing data")
            
            # Delete in reverse order to avoid foreign key constraints
            ResponseTracking.query.delete()
            Activity.query.delete()
            TaskReport.query.delete()
            Curator.query.delete()
            DiscordServer.query.delete()
            # Note: Keep users table intact unless specifically requested
            
            db.session.commit()
        
        # Restore Discord servers first (needed for foreign keys)
        if 'discord_servers' in backup_data['data']:
            servers_data = backup_data['data']['discord_servers']
            for server_data in servers_data:
                # Remove auto-generated fields
                server_data.pop('activity_count', None)
                
                server = DiscordServer(**{
                    k: v for k, v in server_data.items() 
                    if k in ['server_id', 'name', 'role_tag_id', 'is_active']
                })
                
                # Parse datetime fields
                if 'created_at' in server_data and server_data['created_at']:
                    server.created_at = datetime.fromisoformat(server_data['created_at'])
                if 'updated_at' in server_data and server_data['updated_at']:
                    server.updated_at = datetime.fromisoformat(server_data['updated_at'])
                
                db.session.add(server)
            
            db.session.flush()  # Get IDs for foreign keys
            restored_tables.append('discord_servers')
            statistics['discord_servers'] = len(servers_data)
        
        # Restore curators
        if 'curators' in backup_data['data']:
            curators_data = backup_data['data']['curators']
            for curator_data in curators_data:
                curator = Curator(**{
                    k: v for k, v in curator_data.items() 
                    if k in ['discord_id', 'name', 'factions', 'curator_type', 'subdivision', 'total_points', 'rating_level']
                })
                
                # Parse datetime fields
                if 'created_at' in curator_data and curator_data['created_at']:
                    curator.created_at = datetime.fromisoformat(curator_data['created_at'])
                if 'updated_at' in curator_data and curator_data['updated_at']:
                    curator.updated_at = datetime.fromisoformat(curator_data['updated_at'])
                
                db.session.add(curator)
            
            db.session.flush()
            restored_tables.append('curators')
            statistics['curators'] = len(curators_data)
        
        # Create ID mapping for activities restore
        curator_id_map = {}
        for old_id, curator in enumerate(Curator.query.all(), 1):
            curator_id_map[old_id] = curator.id
        
        server_id_map = {}
        for old_id, server in enumerate(DiscordServer.query.all(), 1):
            server_id_map[old_id] = server.id
        
        # Restore activities
        if 'activities' in backup_data['data']:
            activities_data = backup_data['data']['activities']
            for activity_data in activities_data:
                # Map old IDs to new IDs
                old_curator_id = activity_data['curator_id']
                old_server_id = activity_data['server_id']
                
                if old_curator_id in curator_id_map and old_server_id in server_id_map:
                    activity = Activity(
                        curator_id=curator_id_map[old_curator_id],
                        server_id=server_id_map[old_server_id],
                        type=activity_data['type'],
                        content=activity_data.get('content'),
                        points=activity_data.get('points', 0),
                        message_id=activity_data.get('message_id'),
                        channel_id=activity_data.get('channel_id')
                    )
                    
                    if 'timestamp' in activity_data and activity_data['timestamp']:
                        activity.timestamp = datetime.fromisoformat(activity_data['timestamp'])
                    
                    db.session.add(activity)
            
            restored_tables.append('activities')
            statistics['activities'] = len(activities_data)
        
        # Restore response tracking
        if 'response_tracking' in backup_data['data']:
            responses_data = backup_data['data']['response_tracking']
            for response_data in responses_data:
                old_curator_id = response_data['curator_id']
                old_server_id = response_data['server_id']
                
                if old_curator_id in curator_id_map and old_server_id in server_id_map:
                    response = ResponseTracking(
                        curator_id=curator_id_map[old_curator_id],
                        server_id=server_id_map[old_server_id],
                        response_time_seconds=response_data['response_time_seconds'],
                        mention_message_id=response_data.get('mention_message_id'),
                        response_message_id=response_data.get('response_message_id'),
                        channel_id=response_data.get('channel_id'),
                        trigger_keywords=response_data.get('trigger_keywords')
                    )
                    
                    if 'mention_timestamp' in response_data and response_data['mention_timestamp']:
                        response.mention_timestamp = datetime.fromisoformat(response_data['mention_timestamp'])
                    if 'response_timestamp' in response_data and response_data['response_timestamp']:
                        response.response_timestamp = datetime.fromisoformat(response_data['response_timestamp'])
                    
                    db.session.add(response)
            
            restored_tables.append('response_tracking')
            statistics['response_tracking'] = len(responses_data)
        
        # Restore task reports
        if 'task_reports' in backup_data['data']:
            reports_data = backup_data['data']['task_reports']
            for report_data in reports_data:
                report = TaskReport(**{
                    k: v for k, v in report_data.items() 
                    if k in ['author_id', 'author_name', 'task_count', 'approved_tasks', 'rejected_tasks', 
                            'title', 'description', 'notes', 'status']
                })
                
                # Parse datetime fields
                if 'report_date' in report_data and report_data['report_date']:
                    report.report_date = datetime.fromisoformat(report_data['report_date'])
                if 'created_at' in report_data and report_data['created_at']:
                    report.created_at = datetime.fromisoformat(report_data['created_at'])
                if 'updated_at' in report_data and report_data['updated_at']:
                    report.updated_at = datetime.fromisoformat(report_data['updated_at'])
                
                db.session.add(report)
            
            restored_tables.append('task_reports')
            statistics['task_reports'] = len(reports_data)
        
        # Restore users (optional, only if they don't exist)
        if 'users' in backup_data['data'] and force:
            users_data = backup_data['data']['users']
            for user_data in users_data:
                # Check if user already exists
                existing_user = User.find_by_username(user_data['username'])
                if not existing_user:
                    user = User(
                        username=user_data['username'],
                        email=user_data.get('email'),
                        full_name=user_data.get('full_name'),
                        role=user_data.get('role', 'user'),
                        is_active=user_data.get('is_active', True),
                        is_verified=user_data.get('is_verified', False)
                    )
                    
                    # Set a default password (should be changed)
                    user.set_password('changeme123')
                    
                    if 'created_at' in user_data and user_data['created_at']:
                        user.created_at = datetime.fromisoformat(user_data['created_at'])
                    if 'updated_at' in user_data and user_data['updated_at']:
                        user.updated_at = datetime.fromisoformat(user_data['updated_at'])
                    
                    db.session.add(user)
            
            restored_tables.append('users')
            statistics['users'] = len(users_data)
        
        # Commit all changes
        db.session.commit()
        
        logging.info(f"Backup restored successfully: {restored_tables}")
        
        return {
            'success': True,
            'restored_tables': restored_tables,
            'statistics': statistics,
            'backup_metadata': backup_data['metadata']
        }
        
    except Exception as e:
        logging.error(f"Error restoring backup: {e}")
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }

def list_backups():
    """List all available backups"""
    try:
        backup_path = os.environ.get('BACKUP_PATH', './backups')
        
        if not os.path.exists(backup_path):
            return []
        
        backups = []
        
        for filename in os.listdir(backup_path):
            if filename.endswith('.json.gz') or filename.endswith('.json'):
                file_path = os.path.join(backup_path, filename)
                
                try:
                    # Read metadata from backup file
                    if filename.endswith('.gz'):
                        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                            backup_data = json.load(f)
                    else:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            backup_data = json.load(f)
                    
                    metadata = backup_data.get('metadata', {})
                    file_size = os.path.getsize(file_path)
                    
                    backup_info = {
                        'id': metadata.get('id', filename.replace('.json.gz', '').replace('.json', '')),
                        'name': metadata.get('name', filename),
                        'description': metadata.get('description', 'No description'),
                        'created_at': metadata.get('created_at', 'Unknown'),
                        'size': file_size,
                        'file_path': file_path,
                        'statistics': metadata.get('statistics', {})
                    }
                    
                    backups.append(backup_info)
                
                except Exception as e:
                    logging.error(f"Error reading backup file {filename}: {e}")
                    continue
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return backups
        
    except Exception as e:
        logging.error(f"Error listing backups: {e}")
        return []

def delete_backup(backup_id):
    """Delete a specific backup"""
    try:
        backup_path = os.environ.get('BACKUP_PATH', './backups')
        backup_file_path = os.path.join(backup_path, f"{backup_id}.json.gz")
        
        # Also try .json extension
        if not os.path.exists(backup_file_path):
            backup_file_path = os.path.join(backup_path, f"{backup_id}.json")
        
        if not os.path.exists(backup_file_path):
            return {
                'success': False,
                'error': 'Backup file not found'
            }
        
        os.remove(backup_file_path)
        
        logging.info(f"Backup deleted: {backup_id}")
        
        return {
            'success': True,
            'message': f'Backup {backup_id} deleted successfully'
        }
        
    except Exception as e:
        logging.error(f"Error deleting backup: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def create_automatic_backup():
    """Create automatic backup (called by scheduler)"""
    try:
        timestamp = datetime.utcnow()
        backup_name = f"auto_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        result = create_backup(
            name=backup_name,
            description="Automatic scheduled backup",
            include_files=False
        )
        
        if result['success']:
            logging.info(f"Automatic backup created: {backup_name}")
            
            # Clean up old automatic backups (keep last 10)
            cleanup_old_backups()
            
            # Send notification if bot is available
            try:
                from discord_bot.bot import get_bot_instance
                bot = get_bot_instance()
                if bot and bot.notification_manager:
                    import asyncio
                    asyncio.create_task(
                        bot.notification_manager.send_backup_notification(
                            result['backup_info'], 
                            success=True
                        )
                    )
            except Exception as e:
                logging.warning(f"Could not send backup notification: {e}")
        
        else:
            logging.error(f"Automatic backup failed: {result['error']}")
            
            # Send error notification
            try:
                from discord_bot.bot import get_bot_instance
                bot = get_bot_instance()
                if bot and bot.notification_manager:
                    import asyncio
                    asyncio.create_task(
                        bot.notification_manager.send_backup_notification(
                            result, 
                            success=False
                        )
                    )
            except Exception as e:
                logging.warning(f"Could not send backup error notification: {e}")
        
        return result
        
    except Exception as e:
        logging.error(f"Error in automatic backup: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def cleanup_old_backups(keep_count=10):
    """Clean up old automatic backups"""
    try:
        backups = list_backups()
        
        # Filter automatic backups
        auto_backups = [b for b in backups if 'auto_backup_' in b['name']]
        
        if len(auto_backups) <= keep_count:
            return
        
        # Sort by creation date and remove oldest
        auto_backups.sort(key=lambda x: x['created_at'])
        backups_to_delete = auto_backups[:-keep_count]
        
        deleted_count = 0
        for backup in backups_to_delete:
            result = delete_backup(backup['id'])
            if result['success']:
                deleted_count += 1
        
        logging.info(f"Cleaned up {deleted_count} old automatic backups")
        
    except Exception as e:
        logging.error(f"Error cleaning up old backups: {e}")
