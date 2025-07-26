# GovTracker2 Python Migration by Replit Agent
from flask import Blueprint, request, jsonify
from app import db
from models.curator import Curator
from models.activity import Activity
from models.response_tracking import ResponseTracking
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
    """Get specific curator details"""
    try:
        curator = Curator.query.get_or_404(curator_id)
        return jsonify(curator.to_dict())
    except Exception as e:
        logging.error(f"Error getting curator {curator_id}: {e}")
        return jsonify({'error': 'Curator not found'}), 404

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
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if curator with this Discord ID already exists
        existing_curator = Curator.find_by_discord_id(data['discord_id'])
        if existing_curator:
            return jsonify({'error': 'Curator with this Discord ID already exists'}), 409
        
        # Create new curator
        curator = Curator()
        curator.discord_id = str(data['discord_id'])
        curator.name = data['name']
        curator.factions = data.get('factions', [])
        curator.curator_type = data.get('curator_type')
        curator.subdivision = data.get('subdivision')
        curator.total_points = 0
        curator.rating_level = 'Ужасно'
        curator.created_at = datetime.utcnow()
        curator.updated_at = datetime.utcnow()
        
        db.session.add(curator)
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
        if 'factions' in data:
            curator.factions = data['factions']
        if 'curator_type' in data:
            curator.curator_type = data['curator_type']
        if 'subdivision' in data:
            curator.subdivision = data['subdivision']
        
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
