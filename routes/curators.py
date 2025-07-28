# GovTracker2 Python Migration by Replit Agent
from flask import Blueprint, request, jsonify
from app import db
from models.curator import Curator
from models.activity import Activity
from models.response_tracking import ResponseTracking
from models.discord_server import DiscordServer
from utils.rating import calculate_curator_rating
import logging
from datetime import datetime

curators_bp = Blueprint('curators', __name__)

@curators_bp.route('', methods=['GET'])
def get_curators():
    """Get list of all curators"""
    try:
        curators = Curator.query.all()
        curators_data = [curator.to_dict() for curator in curators]
        return jsonify(curators_data)
    except Exception as e:
        logging.error(f"Error getting curators: {e}")
        return jsonify({'error': 'Failed to fetch curators'}), 500

@curators_bp.route('/<int:curator_id>', methods=['GET'])
def get_curator(curator_id):
    """Get specific curator details (fast version)"""
    try:
        curator = Curator.query.get(curator_id)
        if not curator:
            return jsonify({'error': 'Curator not found'}), 404
        
        # Get basic curator data with pre-calculated stats
        curator_data = curator.to_dict()
        
        # Add quick stats without complex calculations
        from models.activity import Activity
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Get last 7 days of activities for quick preview
        since = datetime.utcnow() - timedelta(days=7)
        recent_stats = db.session.query(
            func.count(Activity.id).label('total_activities'),
            func.count(Activity.id).filter(Activity.type == 'message').label('messages'),
            func.count(Activity.id).filter(Activity.type == 'reaction').label('reactions'),
            func.count(Activity.id).filter(Activity.type == 'reply').label('replies'),
            func.sum(Activity.points).label('total_points')
        ).filter(
            Activity.curator_id == curator_id,
            Activity.timestamp >= since
        ).first()
        
        curator_data['weekly_stats'] = {
            'total_activities': recent_stats.total_activities or 0,
            'messages': recent_stats.messages or 0,
            'reactions': recent_stats.reactions or 0,
            'replies': recent_stats.replies or 0,
            'total_points': recent_stats.total_points or 0
        }
        
        return jsonify(curator_data)
        
    except Exception as e:
        logging.error(f"Error getting curator {curator_id}: {e}")
        return jsonify({'error': 'Failed to load curator details'}), 500

@curators_bp.route('/<int:curator_id>/stats', methods=['GET'])
def get_curator_stats(curator_id):
    """Get detailed statistics for a curator"""
    try:
        curator = Curator.query.get_or_404(curator_id)
        
        # Basic curator info
        curator_data = curator.to_dict()
        
        # Activity statistics
        activity_stats = curator.get_activity_stats(days=30)
        
        # Response time statistics
        response_stats = ResponseTracking.get_curator_response_stats(curator_id, days=30)
        
        # Rating calculation
        rating_data = calculate_curator_rating(curator_id)
        
        # Recent activities
        recent_activities = Activity.get_activity_by_curator(curator_id, limit=20)
        recent_activities_data = [activity.to_dict() for activity in recent_activities]
        
        # Monthly breakdown
        monthly_activities = Activity.query.filter_by(curator_id=curator_id).all()
        monthly_breakdown = {}
        for activity in monthly_activities:
            month_key = activity.timestamp.strftime('%Y-%m')
            if month_key not in monthly_breakdown:
                monthly_breakdown[month_key] = {
                    'messages': 0,
                    'reactions': 0,
                    'replies': 0,
                    'task_verifications': 0,
                    'total_points': 0
                }
            monthly_breakdown[month_key][activity.type + 's'] += 1
            monthly_breakdown[month_key]['total_points'] += activity.points
        
        stats_data = {
            'curator': curator_data,
            'activity_stats': activity_stats,
            'response_stats': response_stats,
            'rating_data': rating_data,
            'recent_activities': recent_activities_data,
            'monthly_breakdown': monthly_breakdown
        }
        
        return jsonify(stats_data)
        
    except Exception as e:
        logging.error(f"Error getting curator stats for {curator_id}: {e}")
        return jsonify({'error': 'Failed to fetch curator statistics'}), 500

@curators_bp.route('', methods=['POST'])
def create_curator():
    """Create a new curator"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['discord_id', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Отсутствует обязательное поле: {field}'}), 400
        
        # Check if curator with this Discord ID already exists
        existing_curator = Curator.find_by_discord_id(data['discord_id'])
        if existing_curator:
            return jsonify({'error': 'Куратор с таким Discord ID уже существует'}), 409
        
        # Create new curator
        curator = Curator()
        curator.discord_id = str(data['discord_id'])
        curator.name = data['name']
        curator.total_points = 0
        curator.rating_level = 'Ужасно'
        curator.created_at = datetime.utcnow()
        curator.updated_at = datetime.utcnow()
        
        db.session.add(curator)
        db.session.flush()  # Get the ID before handling servers
        
        # Handle assigned servers
        if 'assigned_servers' in data:
            curator.assigned_servers = data['assigned_servers'] if data['assigned_servers'] else []
        
        db.session.commit()
        
        return jsonify(curator.to_dict()), 201
        
    except Exception as e:
        logging.error(f"Error creating curator: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create curator'}), 500

@curators_bp.route('/<int:curator_id>', methods=['PUT'])
def update_curator(curator_id):
    """Update curator information"""
    try:
        curator = Curator.query.get_or_404(curator_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            curator.name = data['name']
        if 'assigned_servers' in data:
            # Store server IDs as JSON array
            curator.assigned_servers = data['assigned_servers'] if data['assigned_servers'] else []
        if 'curator_type' in data:
            curator.curator_type = data['curator_type']
        if 'subdivision' in data:
            curator.subdivision = data['subdivision']
        
        curator.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(curator.to_dict())
        
    except Exception as e:
        logging.error(f"Error updating curator {curator_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update curator'}), 500

@curators_bp.route('/<int:curator_id>', methods=['DELETE'])
def delete_curator(curator_id):
    """Delete a curator"""
    try:
        curator = Curator.query.get_or_404(curator_id)
        
        # Delete associated activities and response tracking
        Activity.query.filter_by(curator_id=curator_id).delete()
        ResponseTracking.query.filter_by(curator_id=curator_id).delete()
        
        db.session.delete(curator)
        db.session.commit()
        
        return jsonify({'message': 'Curator deleted successfully'})
        
    except Exception as e:
        logging.error(f"Error deleting curator {curator_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete curator'}), 500

@curators_bp.route('/search', methods=['GET'])
def search_curators():
    """Search curators by name or Discord ID"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify([])
        
        curators = Curator.query.filter(
            db.or_(
                Curator.name.ilike(f'%{query}%'),
                Curator.discord_id.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        return jsonify([curator.to_dict() for curator in curators])
        
    except Exception as e:
        logging.error(f"Error searching curators: {e}")
        return jsonify({'error': 'Search failed'}), 500

@curators_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get curator leaderboard"""
    try:
        limit = request.args.get('limit', 20, type=int)
        period = request.args.get('period', 'all')  # all, month, week
        
        query = Curator.query.order_by(Curator.total_points.desc())
        
        if period == 'month':
            # Filter by activities in the last month
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # This would require a more complex query to calculate monthly points
            # For now, return all-time leaderboard
            pass
        
        curators = query.limit(limit).all()
        
        leaderboard_data = []
        for rank, curator in enumerate(curators, 1):
            curator_data = curator.to_dict()
            curator_data['rank'] = rank
            curator_data['activity_stats'] = curator.get_activity_stats(days=30)
            leaderboard_data.append(curator_data)
        
        return jsonify(leaderboard_data)
        
    except Exception as e:
        logging.error(f"Error getting leaderboard: {e}")
        return jsonify({'error': 'Failed to fetch leaderboard'}), 500

@curators_bp.route('/<int:curator_id>/details', methods=['GET'])
def get_curator_details(curator_id):
    """Get comprehensive curator details for the details page"""
    try:
        curator = Curator.query.get_or_404(curator_id)
        
        # Basic curator info
        curator_data = curator.to_dict()
        
        # Extended activity statistics
        try:
            activity_stats = curator.get_activity_stats(days=30)
            activity_stats_all_time = curator.get_activity_stats(days=None) if hasattr(curator, 'get_activity_stats') else {}
        except:
            activity_stats = {'total_activities': 0, 'messages': 0, 'reactions': 0, 'replies': 0, 'task_verifications': 0}
            activity_stats_all_time = {'total_activities': 0, 'messages': 0, 'reactions': 0, 'replies': 0, 'task_verifications': 0}
        
        # Response time statistics  
        try:
            response_stats = ResponseTracking.get_curator_response_stats(curator_id, days=30) if hasattr(ResponseTracking, 'get_curator_response_stats') else {}
        except:
            response_stats = {'average_response_time': 0, 'total_responses': 0, 'good_responses': 0, 'poor_responses': 0}
        
        # Rating calculation and breakdown
        from utils.rating import calculate_curator_rating
        rating_data = calculate_curator_rating(curator_id)
        
        # Recent activities with details
        try:
            recent_activities = Activity.query.filter_by(curator_id=curator_id).order_by(Activity.timestamp.desc()).limit(50).all()
            recent_activities_data = []
            for activity in recent_activities:
                activity_dict = activity.to_dict()
                # Add server name
                if hasattr(activity, 'discord_server') and activity.discord_server:
                    activity_dict['server_name'] = activity.discord_server.name
                recent_activities_data.append(activity_dict)
        except:
            recent_activities_data = []
        
        # Monthly performance breakdown
        from datetime import datetime, timedelta
        from sqlalchemy import func, extract
        
        # Get activities for the last 12 months
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        monthly_data = db.session.query(
            extract('year', Activity.timestamp).label('year'),
            extract('month', Activity.timestamp).label('month'),
            Activity.type,
            func.count(Activity.id).label('count'),
            func.sum(Activity.points).label('points')
        ).filter(
            Activity.curator_id == curator_id,
            Activity.timestamp >= twelve_months_ago
        ).group_by(
            extract('year', Activity.timestamp),
            extract('month', Activity.timestamp),
            Activity.type
        ).all()
        
        # Organize monthly data
        monthly_breakdown = {}
        for data in monthly_data:
            month_key = f"{int(data.year)}-{int(data.month):02d}"
            if month_key not in monthly_breakdown:
                monthly_breakdown[month_key] = {
                    'messages': 0, 'reactions': 0, 'replies': 0, 
                    'task_verifications': 0, 'total_points': 0
                }
            monthly_breakdown[month_key][f"{data.type}s"] = data.count
            monthly_breakdown[month_key]['total_points'] += data.points or 0
        
        # Server activity breakdown
        server_activities = db.session.query(
            Activity.server_id,
            func.count(Activity.id).label('activity_count'),
            func.sum(Activity.points).label('total_points')
        ).filter(
            Activity.curator_id == curator_id
        ).group_by(Activity.server_id).all()
        
        server_breakdown = []
        for server_data in server_activities:
            server = DiscordServer.query.get(server_data.server_id)
            if server:
                server_breakdown.append({
                    'server_id': server.id,
                    'server_name': server.name,
                    'activity_count': server_data.activity_count,
                    'total_points': server_data.total_points or 0
                })
        
        # Assigned servers details
        assigned_servers_details = []
        if curator.assigned_servers:
            for server_id in curator.assigned_servers:
                try:
                    server = DiscordServer.query.get(int(server_id))
                    if server:
                        assigned_servers_details.append(server.to_dict())
                except (ValueError, TypeError):
                    continue
        
        details_data = {
            'curator': curator_data,
            'activity_stats': activity_stats,
            'activity_stats_all_time': activity_stats_all_time,
            'response_stats': response_stats,
            'rating_data': rating_data,
            'recent_activities': recent_activities_data,
            'monthly_breakdown': monthly_breakdown,
            'server_breakdown': server_breakdown,
            'assigned_servers_details': assigned_servers_details
        }
        
        return jsonify(details_data)
        
    except Exception as e:
        logging.error(f"Error getting curator details for {curator_id}: {e}")
        return jsonify({'error': 'Failed to fetch curator details'}), 500
