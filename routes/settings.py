# GovTracker2 Python Migration by Replit Agent
from flask import Blueprint, request, jsonify
from database import db
import logging
import os

settings_bp = Blueprint('settings', __name__)

# Default settings configuration
DEFAULT_SETTINGS = {
    'discord_bot': {
        'token': '',
        'max_servers': 8,
        'monitoring_enabled': True,
        'response_tracking': True,
        'notification_roles': []
    },
    'rating_system': {
        'points': {
            'message': 3,
            'reaction': 1,
            'reply': 2,
            'task_verification': 5
        },
        'levels': {
            'excellent': 50,
            'good': 35,
            'normal': 20,
            'poor': 10,
            'terrible': 0
        },
        'response_time': {
            'good_threshold': 60,
            'poor_threshold': 300
        }
    },
    'backup': {
        'auto_backup': True,
        'backup_frequency': 'daily',
        'retention_days': 30,
        'backup_path': './backups'
    },
    'ui': {
        'theme': 'auto',
        'items_per_page': 50,
        'refresh_interval': 30,
        'enable_animations': True
    },
    'notifications': {
        'email_notifications': False,
        'webhook_url': '',
        'notification_types': ['error', 'backup', 'system'],
        'curator_reminder_time': 300,  # seconds until reminder
        'auto_reminder': True  # repeat reminder after same time interval
    },
    'database': {
        'type': 'postgresql',
        'connection_pool_size': 10,
        'query_timeout': 30
    }
}

@settings_bp.route('', methods=['GET'])
def get_settings():
    """Get current application settings"""
    try:
        # In a real application, these would be stored in database or config files
        # For now, we'll return default settings merged with environment variables
        
        settings = DEFAULT_SETTINGS.copy()
        
        # Override with environment variables if available
        if os.environ.get('DISCORD_TOKEN'):
            settings['discord_bot']['token'] = os.environ.get('DISCORD_TOKEN')
        
        if os.environ.get('BACKUP_PATH'):
            settings['backup']['backup_path'] = os.environ.get('BACKUP_PATH')
        
        if os.environ.get('DATABASE_URL'):
            if 'mysql' in os.environ.get('DATABASE_URL'):
                settings['database']['type'] = 'mysql'
            else:
                settings['database']['type'] = 'postgresql'
        
        return jsonify(settings)
        
    except Exception as e:
        logging.error(f"Error getting settings: {e}")
        return jsonify({'error': 'Failed to fetch settings'}), 500

@settings_bp.route('', methods=['PUT'])
def update_settings():
    """Update application settings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No settings data provided'}), 400
        
        # Validate settings structure
        valid_sections = ['discord_bot', 'rating_system', 'backup', 'ui', 'notifications', 'database']
        
        for section in data.keys():
            if section not in valid_sections:
                return jsonify({'error': f'Invalid settings section: {section}'}), 400
        
        # Validate specific settings
        if 'discord_bot' in data:
            discord_settings = data['discord_bot']
            if 'max_servers' in discord_settings:
                if not isinstance(discord_settings['max_servers'], int) or discord_settings['max_servers'] < 1 or discord_settings['max_servers'] > 20:
                    return jsonify({'error': 'max_servers must be between 1 and 20'}), 400
        
        if 'rating_system' in data:
            rating_settings = data['rating_system']
            if 'points' in rating_settings:
                points = rating_settings['points']
                for activity_type, point_value in points.items():
                    if not isinstance(point_value, int) or point_value < 0:
                        return jsonify({'error': f'Invalid point value for {activity_type}'}), 400
        
        # In a real application, you would save these to database or config files
        # For now, we'll just return success
        
        # Merge with existing settings
        current_settings = DEFAULT_SETTINGS.copy()
        
        def deep_merge(dict1, dict2):
            """Recursively merge two dictionaries"""
            for key, value in dict2.items():
                if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                    deep_merge(dict1[key], value)
                else:
                    dict1[key] = value
        
        deep_merge(current_settings, data)
        
        return jsonify({
            'message': 'Settings updated successfully',
            'settings': current_settings
        })
        
    except Exception as e:
        logging.error(f"Error updating settings: {e}")
        return jsonify({'error': 'Failed to update settings'}), 500

@settings_bp.route('/reset', methods=['POST'])
def reset_settings():
    """Reset settings to default values"""
    try:
        section = request.args.get('section')
        
        if section:
            if section not in DEFAULT_SETTINGS:
                return jsonify({'error': f'Invalid settings section: {section}'}), 400
            
            # Reset only the specified section
            reset_data = {section: DEFAULT_SETTINGS[section]}
            message = f'Settings section "{section}" reset to defaults'
        else:
            # Reset all settings
            reset_data = DEFAULT_SETTINGS.copy()
            message = 'All settings reset to defaults'
        
        # In a real application, you would save this to database or config files
        
        return jsonify({
            'message': message,
            'settings': reset_data
        })
        
    except Exception as e:
        logging.error(f"Error resetting settings: {e}")
        return jsonify({'error': 'Failed to reset settings'}), 500

@settings_bp.route('/validate', methods=['POST'])
def validate_settings():
    """Validate settings without saving"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No settings data provided'}), 400
        
        validation_errors = []
        
        # Validate Discord bot settings
        if 'discord_bot' in data:
            discord_settings = data['discord_bot']
            
            if 'token' in discord_settings and discord_settings['token']:
                token = discord_settings['token']
                if not token.startswith('Bot ') and len(token) < 50:
                    validation_errors.append('Discord token appears to be invalid')
            
            if 'max_servers' in discord_settings:
                max_servers = discord_settings['max_servers']
                if not isinstance(max_servers, int) or max_servers < 1 or max_servers > 20:
                    validation_errors.append('max_servers must be between 1 and 20')
        
        # Validate rating system settings
        if 'rating_system' in data:
            rating_settings = data['rating_system']
            
            if 'points' in rating_settings:
                points = rating_settings['points']
                required_activities = ['message', 'reaction', 'reply', 'task_verification']
                
                for activity in required_activities:
                    if activity not in points:
                        validation_errors.append(f'Missing point value for {activity}')
                    elif not isinstance(points[activity], int) or points[activity] < 0:
                        validation_errors.append(f'Invalid point value for {activity}')
            
            if 'response_time' in rating_settings:
                response_time = rating_settings['response_time']
                if 'good_threshold' in response_time and 'poor_threshold' in response_time:
                    if response_time['good_threshold'] >= response_time['poor_threshold']:
                        validation_errors.append('good_threshold must be less than poor_threshold')
        
        # Validate backup settings
        if 'backup' in data:
            backup_settings = data['backup']
            
            if 'backup_frequency' in backup_settings:
                valid_frequencies = ['hourly', 'daily', 'weekly', 'monthly']
                if backup_settings['backup_frequency'] not in valid_frequencies:
                    validation_errors.append(f'backup_frequency must be one of: {valid_frequencies}')
            
            if 'retention_days' in backup_settings:
                retention = backup_settings['retention_days']
                if not isinstance(retention, int) or retention < 1:
                    validation_errors.append('retention_days must be a positive integer')
        
        if validation_errors:
            return jsonify({
                'valid': False,
                'errors': validation_errors
            }), 400
        
        return jsonify({
            'valid': True,
            'message': 'Settings validation passed'
        })
        
    except Exception as e:
        logging.error(f"Error validating settings: {e}")
        return jsonify({'error': 'Failed to validate settings'}), 500

@settings_bp.route('/export', methods=['GET'])
def export_settings():
    """Export current settings as JSON"""
    try:
        # Get current settings
        settings = DEFAULT_SETTINGS.copy()
        
        # Remove sensitive information
        if 'discord_bot' in settings and 'token' in settings['discord_bot']:
            settings['discord_bot']['token'] = '***REDACTED***'
        
        return jsonify(settings), 200, {
            'Content-Type': 'application/json',
            'Content-Disposition': 'attachment; filename=govtracker2_settings.json'
        }
        
    except Exception as e:
        logging.error(f"Error exporting settings: {e}")
        return jsonify({'error': 'Failed to export settings'}), 500

@settings_bp.route('/import', methods=['POST'])
def import_settings():
    """Import settings from JSON"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No settings data provided'}), 400
        
        # Validate imported settings
        validation_response = validate_settings()
        if validation_response[1] == 400:  # Validation failed
            return validation_response
        
        # In a real application, you would save these settings
        
        return jsonify({
            'message': 'Settings imported successfully',
            'imported_sections': list(data.keys())
        })
        
    except Exception as e:
        logging.error(f"Error importing settings: {e}")
        return jsonify({'error': 'Failed to import settings'}), 500
