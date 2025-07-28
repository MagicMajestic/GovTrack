# GovTracker2 Python Migration by Replit Agent
from flask import Blueprint, request, jsonify
from app import db
from models.discord_server import DiscordServer
from models.activity import Activity
import logging
from datetime import datetime

servers_bp = Blueprint('servers', __name__)

@servers_bp.route('', methods=['GET'])
def get_servers():
    """Get list of all Discord servers"""
    try:
        # Use a separate session to avoid transaction conflicts
        servers = DiscordServer.query.all()
        servers_data = []
        
        for server in servers:
            try:
                # Get basic server data with safer statistics calculation
                server_dict = {
                    'id': server.id,
                    'server_id': server.server_id,
                    'name': server.name,
                    'curator_role_id': server.curator_role_id,
                    'notification_channel_id': server.notification_channel_id,
                    'tasks_channel_id': server.tasks_channel_id,
                    'is_active': server.is_active,
                    'created_at': server.created_at.isoformat() if server.created_at else None,
                    'updated_at': server.updated_at.isoformat() if server.updated_at else None,
                    'activity_count': 0,
                    'curator_count': 0,
                    'avg_response_time': 0,
                    'reactions_count': 0
                }
                
                # Try to get statistics, but don't fail if they error
                try:
                    server_dict['activity_count'] = server.get_activity_count()
                except:
                    pass
                    
                try:
                    server_dict['curator_count'] = server.get_curator_count()
                except:
                    pass
                    
                try:
                    server_dict['reactions_count'] = server.get_reactions_count()
                except:
                    pass
                
                servers_data.append(server_dict)
                
            except Exception as e:
                logging.warning(f"Error processing server {server.id}: {e}")
                # Add basic server info even if stats fail
                servers_data.append({
                    'id': server.id,
                    'server_id': server.server_id,
                    'name': server.name,
                    'is_active': server.is_active,
                    'activity_count': 0,
                    'curator_count': 0,
                    'avg_response_time': 0,
                    'reactions_count': 0
                })
                
        return jsonify(servers_data)
        
    except Exception as e:
        logging.error(f"Error getting servers: {e}")
        return jsonify({'error': 'Failed to fetch servers'}), 500

@servers_bp.route('/<int:server_id>', methods=['GET'])
def get_server(server_id):
    """Get specific server details"""
    try:
        server = DiscordServer.query.get_or_404(server_id)
        return jsonify(server.to_dict())
    except Exception as e:
        logging.error(f"Error getting server {server_id}: {e}")
        return jsonify({'error': 'Server not found'}), 404

@servers_bp.route('', methods=['POST'])
def create_server():
    """Add a new Discord server"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['server_id', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Отсутствует обязательное поле: {field}'}), 400
        
        # Check if server with this ID already exists
        existing_server = DiscordServer.find_by_server_id(data['server_id'])
        if existing_server:
            return jsonify({'error': 'Сервер с таким ID уже существует'}), 409
        
        # Create new server
        server = DiscordServer()
        server.server_id = str(data['server_id'])
        server.name = data['name']
        server.curator_role_id = data.get('curator_role_id')
        server.notification_channel_id = data.get('notification_channel_id')
        server.tasks_channel_id = data.get('tasks_channel_id')
        server.is_active = data.get('is_active', True)
        server.created_at = datetime.utcnow()
        server.updated_at = datetime.utcnow()
        
        db.session.add(server)
        db.session.commit()
        
        return jsonify(server.to_dict()), 201
        
    except Exception as e:
        logging.error(f"Error creating server: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create server'}), 500

@servers_bp.route('/<int:server_id>', methods=['PUT'])
def update_server(server_id):
    """Update server information"""
    try:
        server = DiscordServer.query.get_or_404(server_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            server.name = data['name']
        if 'curator_role_id' in data:
            server.curator_role_id = data['curator_role_id']
        if 'notification_channel_id' in data:
            server.notification_channel_id = data['notification_channel_id']
        if 'tasks_channel_id' in data:
            server.tasks_channel_id = data['tasks_channel_id']
        if 'is_active' in data:
            server.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify(server.to_dict())
        
    except Exception as e:
        logging.error(f"Error updating server {server_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update server'}), 500

@servers_bp.route('/<int:server_id>', methods=['DELETE'])
def delete_server(server_id):
    """Delete a Discord server"""
    try:
        server = DiscordServer.query.get_or_404(server_id)
        
        # Delete associated activities
        Activity.query.filter_by(server_id=server_id).delete()
        
        db.session.delete(server)
        db.session.commit()
        
        return jsonify({'message': 'Server deleted successfully'})
        
    except Exception as e:
        logging.error(f"Error deleting server {server_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete server'}), 500

@servers_bp.route('/<int:server_id>/stats', methods=['GET'])
def get_server_stats(server_id):
    """Get detailed statistics for a server"""
    try:
        server = DiscordServer.query.get_or_404(server_id)
        
        # Basic server info
        server_data = server.to_dict()
        
        # Activity statistics
        total_activities = server.get_activity_count()
        recent_activities = server.get_activity_count(days=30)
        
        # Active curators
        active_curators = server.get_active_curators()
        curator_data = [
            {
                'id': curator.id,
                'name': curator.name,
                'discord_id': curator.discord_id,
                'total_points': curator.total_points
            }
            for curator in active_curators
        ]
        
        # Activity breakdown by type
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        activity_breakdown = db.session.query(
            Activity.type,
            func.count(Activity.id).label('count')
        ).filter(
            Activity.server_id == server_id,
            Activity.timestamp >= cutoff_date
        ).group_by(Activity.type).all()
        
        breakdown_data = {}
        for item in activity_breakdown:
            breakdown_data[item.type] = item.count
        
        # Daily activity trend
        daily_trend = db.session.query(
            func.date(Activity.timestamp).label('date'),
            func.count(Activity.id).label('count')
        ).filter(
            Activity.server_id == server_id,
            Activity.timestamp >= cutoff_date
        ).group_by(func.date(Activity.timestamp)).all()
        
        trend_data = [
            {
                'date': str(item.date),
                'count': item.count
            }
            for item in daily_trend
        ]
        
        stats_data = {
            'server': server_data,
            'total_activities': total_activities,
            'recent_activities': recent_activities,
            'active_curators': curator_data,
            'activity_breakdown': breakdown_data,
            'daily_trend': trend_data
        }
        
        return jsonify(stats_data)
        
    except Exception as e:
        logging.error(f"Error getting server stats for {server_id}: {e}")
        return jsonify({'error': 'Failed to fetch server statistics'}), 500

@servers_bp.route('/<int:server_id>/activities', methods=['GET'])
def get_server_activities(server_id):
    """Get activities for a specific server"""
    try:
        server = DiscordServer.query.get_or_404(server_id)
        limit = request.args.get('limit', 100, type=int)
        
        activities = Activity.get_activity_by_server(server_id, limit=limit)
        activities_data = [activity.to_dict() for activity in activities]
        
        return jsonify({
            'server_id': server_id,
            'server_name': server.name,
            'activities': activities_data
        })
        
    except Exception as e:
        logging.error(f"Error getting activities for server {server_id}: {e}")
        return jsonify({'error': 'Failed to fetch server activities'}), 500

@servers_bp.route('/active', methods=['GET'])
def get_active_servers():
    """Get only active servers"""
    try:
        servers = DiscordServer.get_active_servers()
        servers_data = [server.to_dict() for server in servers]
        return jsonify(servers_data)
    except Exception as e:
        logging.error(f"Error getting active servers: {e}")
        return jsonify({'error': 'Failed to fetch active servers'}), 500

@servers_bp.route('/initialize', methods=['POST'])
def initialize_default_servers():
    """Initialize default Discord servers (factions)"""
    try:
        default_servers = [
            {'server_id': '916616528395378708', 'name': 'Detectives'},
            {'server_id': '1329213276587950080', 'name': 'Weazel News'},
            {'server_id': '1329212940540313644', 'name': 'EMS'},
            {'server_id': '1329213185579946106', 'name': 'LSCSD'},
            {'server_id': '1329213239996973116', 'name': 'SANG'},
            {'server_id': '1329212725921976322', 'name': 'LSPD'},
            {'server_id': '1329213307059437629', 'name': 'FIB'},
            {'server_id': '1329213001814773780', 'name': 'Government'},
        ]
        
        created_servers = []
        for server_data in default_servers:
            # Check if server already exists
            existing_server = DiscordServer.find_by_server_id(server_data['server_id'])
            if existing_server:
                continue
                
            # Create new server
            server = DiscordServer()
            server.server_id = server_data['server_id']
            server.name = server_data['name']
            server.is_active = True
            server.created_at = datetime.utcnow()
            server.updated_at = datetime.utcnow()
            
            db.session.add(server)
            created_servers.append(server_data['name'])
        
        db.session.commit()
        
        return jsonify({
            'message': f'Инициализировано серверов: {len(created_servers)}',
            'created_servers': created_servers
        })
        
    except Exception as e:
        logging.error(f"Error initializing servers: {e}")
        db.session.rollback()
        return jsonify({'error': 'Ошибка инициализации серверов'}), 500

@servers_bp.route('/<int:server_id>/toggle-status', methods=['POST'])
def toggle_server_status(server_id):
    """Toggle server active status"""
    try:
        server = DiscordServer.query.get_or_404(server_id)
        server.is_active = not server.is_active
        
        db.session.commit()
        
        return jsonify({
            'message': f'Server {"activated" if server.is_active else "deactivated"} successfully',
            'server': server.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error toggling server status for {server_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to toggle server status'}), 500
