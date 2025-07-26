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
        servers = DiscordServer.query.all()
        servers_data = [server.to_dict() for server in servers]
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
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if server with this ID already exists
        existing_server = DiscordServer.find_by_server_id(data['server_id'])
        if existing_server:
            return jsonify({'error': 'Server with this ID already exists'}), 409
        
        # Create new server
        server = DiscordServer()
        server.server_id = str(data['server_id'])
        server.name = data['name']
        server.role_tag_id = data.get('role_tag_id')
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
        if 'role_tag_id' in data:
            server.role_tag_id = data['role_tag_id']
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
