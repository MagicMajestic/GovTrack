# GovTracker2 Python Migration by Replit Agent
from flask import Blueprint, request, jsonify, send_file
from utils.backup_service import create_backup, restore_from_backup, list_backups, delete_backup
import logging
import os

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/create', methods=['POST'])
def create_backup_endpoint():
    """Create a new backup"""
    try:
        data = request.get_json() or {}
        
        # Optional backup name and description
        backup_name = data.get('name')
        description = data.get('description', 'Manual backup')
        include_files = data.get('include_files', False)
        
        # Create backup
        backup_result = create_backup(
            name=backup_name,
            description=description,
            include_files=include_files
        )
        
        if backup_result['success']:
            return jsonify({
                'message': 'Backup created successfully',
                'backup': backup_result['backup_info']
            }), 201
        else:
            return jsonify({
                'error': 'Failed to create backup',
                'details': backup_result['error']
            }), 500
        
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        return jsonify({'error': 'Failed to create backup'}), 500

@backup_bp.route('/restore', methods=['POST'])
def restore_backup_endpoint():
    """Restore from a backup"""
    try:
        data = request.get_json()
        
        if not data or 'backup_id' not in data:
            return jsonify({'error': 'backup_id is required'}), 400
        
        backup_id = data['backup_id']
        force_restore = data.get('force', False)
        
        # Restore from backup
        restore_result = restore_from_backup(backup_id, force=force_restore)
        
        if restore_result['success']:
            return jsonify({
                'message': 'Backup restored successfully',
                'restored_tables': restore_result['restored_tables'],
                'statistics': restore_result['statistics']
            })
        else:
            return jsonify({
                'error': 'Failed to restore backup',
                'details': restore_result['error']
            }), 500
        
    except Exception as e:
        logging.error(f"Error restoring backup: {e}")
        return jsonify({'error': 'Failed to restore backup'}), 500

@backup_bp.route('/list', methods=['GET'])
def list_backups_endpoint():
    """List available backups"""
    try:
        backups = list_backups()
        return jsonify(backups)
        
    except Exception as e:
        logging.error(f"Error listing backups: {e}")
        return jsonify({'error': 'Failed to list backups'}), 500

@backup_bp.route('/<backup_id>', methods=['DELETE'])
def delete_backup_endpoint(backup_id):
    """Delete a specific backup"""
    try:
        result = delete_backup(backup_id)
        
        if result['success']:
            return jsonify({
                'message': 'Backup deleted successfully'
            })
        else:
            return jsonify({
                'error': 'Failed to delete backup',
                'details': result['error']
            }), 500
        
    except Exception as e:
        logging.error(f"Error deleting backup {backup_id}: {e}")
        return jsonify({'error': 'Failed to delete backup'}), 500

@backup_bp.route('/<backup_id>/download', methods=['GET'])
def download_backup(backup_id):
    """Download a backup file"""
    try:
        backup_path = os.path.join(os.environ.get('BACKUP_PATH', './backups'), f'{backup_id}.json')
        
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404
        
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=f'govtracker2_backup_{backup_id}.json',
            mimetype='application/json'
        )
        
    except Exception as e:
        logging.error(f"Error downloading backup {backup_id}: {e}")
        return jsonify({'error': 'Failed to download backup'}), 500

@backup_bp.route('/upload', methods=['POST'])
def upload_backup():
    """Upload and restore from backup file"""
    try:
        if 'backup_file' not in request.files:
            return jsonify({'error': 'No backup file provided'}), 400
        
        file = request.files['backup_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file temporarily
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
            file_content = file.read().decode('utf-8')
            
            # Validate JSON format
            try:
                backup_data = json.loads(file_content)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON format'}), 400
            
            # Validate backup structure
            required_fields = ['metadata', 'data']
            for field in required_fields:
                if field not in backup_data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Restore from uploaded file
            force_restore = request.form.get('force', 'false').lower() == 'true'
            restore_result = restore_from_backup(temp_file_path, force=force_restore, is_file_path=True)
            
            if restore_result['success']:
                return jsonify({
                    'message': 'Backup uploaded and restored successfully',
                    'restored_tables': restore_result['restored_tables'],
                    'statistics': restore_result['statistics']
                })
            else:
                return jsonify({
                    'error': 'Failed to restore uploaded backup',
                    'details': restore_result['error']
                }), 500
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logging.error(f"Error uploading backup: {e}")
        return jsonify({'error': 'Failed to upload backup'}), 500

@backup_bp.route('/schedule', methods=['GET'])
def get_backup_schedule():
    """Get current backup schedule configuration"""
    try:
        from scheduler import get_scheduler
        
        scheduler = get_scheduler()
        if not scheduler:
            return jsonify({'error': 'Scheduler not initialized'}), 500
        
        # Get backup job information
        backup_job = scheduler.get_job('daily_backup')
        
        if backup_job:
            next_run = backup_job.next_run_time.isoformat() if backup_job.next_run_time else None
            schedule_info = {
                'enabled': True,
                'job_id': backup_job.id,
                'next_run': next_run,
                'trigger': str(backup_job.trigger)
            }
        else:
            schedule_info = {
                'enabled': False,
                'job_id': None,
                'next_run': None,
                'trigger': None
            }
        
        return jsonify(schedule_info)
        
    except Exception as e:
        logging.error(f"Error getting backup schedule: {e}")
        return jsonify({'error': 'Failed to get backup schedule'}), 500

@backup_bp.route('/schedule', methods=['PUT'])
def update_backup_schedule():
    """Update backup schedule configuration"""
    try:
        data = request.get_json()
        
        if not data or 'enabled' not in data:
            return jsonify({'error': 'enabled field is required'}), 400
        
        from scheduler import get_scheduler
        from utils.backup_service import create_automatic_backup
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = get_scheduler()
        if not scheduler:
            return jsonify({'error': 'Scheduler not initialized'}), 500
        
        enabled = data['enabled']
        
        if enabled:
            # Enable or update backup schedule
            hour = data.get('hour', 2)
            minute = data.get('minute', 0)
            
            # Remove existing job if it exists
            try:
                scheduler.remove_job('daily_backup')
            except:
                pass
            
            # Add new job
            scheduler.add_job(
                func=create_automatic_backup,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_backup',
                name='Daily automatic backup',
                replace_existing=True
            )
            
            message = f'Backup scheduled daily at {hour:02d}:{minute:02d}'
        
        else:
            # Disable backup schedule
            try:
                scheduler.remove_job('daily_backup')
                message = 'Automatic backup disabled'
            except:
                message = 'Backup was not scheduled'
        
        return jsonify({
            'message': message,
            'enabled': enabled
        })
        
    except Exception as e:
        logging.error(f"Error updating backup schedule: {e}")
        return jsonify({'error': 'Failed to update backup schedule'}), 500

@backup_bp.route('/stats', methods=['GET'])
def get_backup_stats():
    """Get backup statistics and information"""
    try:
        backups = list_backups()
        
        if not backups:
            return jsonify({
                'total_backups': 0,
                'total_size': 0,
                'oldest_backup': None,
                'newest_backup': None,
                'disk_usage': {
                    'used': 0,
                    'available': 'unknown'
                }
            })
        
        # Calculate statistics
        total_backups = len(backups)
        total_size = sum(backup.get('size', 0) for backup in backups)
        
        # Sort by creation date
        sorted_backups = sorted(backups, key=lambda x: x.get('created_at', ''))
        oldest_backup = sorted_backups[0]['created_at'] if sorted_backups else None
        newest_backup = sorted_backups[-1]['created_at'] if sorted_backups else None
        
        # Get disk usage
        backup_path = os.environ.get('BACKUP_PATH', './backups')
        disk_usage = {'used': total_size, 'available': 'unknown'}
        
        try:
            import shutil
            total, used, free = shutil.disk_usage(backup_path)
            disk_usage['available'] = free
        except:
            pass
        
        stats = {
            'total_backups': total_backups,
            'total_size': total_size,
            'oldest_backup': oldest_backup,
            'newest_backup': newest_backup,
            'disk_usage': disk_usage,
            'backup_path': backup_path
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logging.error(f"Error getting backup stats: {e}")
        return jsonify({'error': 'Failed to get backup statistics'}), 500
