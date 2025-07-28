# GovTracker2 Python Migration by Replit Agent
from flask import Blueprint, request, jsonify
from app import db
from models.activity import Activity
from models.curator import Curator
from models.discord_server import DiscordServer
from config import Config
import logging
from datetime import datetime

activities_bp = Blueprint('activities', __name__)

@activities_bp.route('', methods=['GET'])
def get_activities():
    """Get all activities (main endpoint)"""
    try:
        limit = request.args.get('limit', 100, type=int)
        server_id = request.args.get('server_id', type=int)
        curator_id = request.args.get('curator_id', type=int)
        activity_type = request.args.get('type')
        
        query = Activity.query
        
        # Apply filters
        if server_id:
            query = query.filter_by(server_id=server_id)
        
        if curator_id:
            query = query.filter_by(curator_id=curator_id)
        
        if activity_type:
            query = query.filter_by(type=activity_type)
        
        activities = query.order_by(Activity.timestamp.desc()).limit(limit).all()
        activities_data = [activity.to_dict() for activity in activities]
        
        return jsonify(activities_data)
        
    except Exception as e:
        logging.error(f"Error getting activities: {e}")
        return jsonify({'error': 'Failed to fetch activities'}), 500

@activities_bp.route('/recent', methods=['GET'])
def get_recent_activities():
    """Get recent activities with optional filtering"""
    try:
        limit = request.args.get('limit', 50, type=int)
        server_id = request.args.get('server_id', type=int)
        curator_id = request.args.get('curator_id', type=int)
        activity_type = request.args.get('type')
        
        query = Activity.query
        
        # Apply filters
        if server_id:
            query = query.filter_by(server_id=server_id)
        
        if curator_id:
            query = query.filter_by(curator_id=curator_id)
        
        if activity_type:
            query = query.filter_by(type=activity_type)
        
        activities = query.order_by(Activity.timestamp.desc()).limit(limit).all()
        activities_data = [activity.to_dict() for activity in activities]
        
        return jsonify(activities_data)
        
    except Exception as e:
        logging.error(f"Error getting recent activities: {e}")
        return jsonify({'error': 'Failed to fetch recent activities'}), 500

@activities_bp.route('/daily', methods=['GET'])
def get_daily_activities():
    """Get daily activity statistics"""
    try:
        days = request.args.get('days', 30, type=int)
        server_id = request.args.get('server_id', type=int)
        curator_id = request.args.get('curator_id', type=int)
        
        # Get base daily stats
        daily_stats = Activity.get_daily_stats(days=days)
        
        # Apply additional filtering if needed
        if server_id or curator_id:
            from datetime import datetime, timedelta
            from sqlalchemy import func
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = db.session.query(
                func.date(Activity.timestamp).label('date'),
                func.count(Activity.id).label('count'),
                Activity.type
            ).filter(Activity.timestamp >= cutoff_date)
            
            if server_id:
                query = query.filter(Activity.server_id == server_id)
            
            if curator_id:
                query = query.filter(Activity.curator_id == curator_id)
            
            filtered_stats = query.group_by(
                func.date(Activity.timestamp),
                Activity.type
            ).all()
            
            # Reformat filtered results
            result = {}
            for stat in filtered_stats:
                date_str = str(stat.date)
                if date_str not in result:
                    result[date_str] = {
                        'date': date_str,
                        'total': 0,
                        'messages': 0,
                        'reactions': 0,
                        'replies': 0,
                        'task_verifications': 0
                    }
                
                result[date_str][stat.type + 's'] = stat.count
                result[date_str]['total'] += stat.count
            
            daily_stats = list(result.values())
        
        return jsonify(daily_stats)
        
    except Exception as e:
        logging.error(f"Error getting daily activities: {e}")
        return jsonify({'error': 'Failed to fetch daily activities'}), 500

@activities_bp.route('', methods=['POST'])
def create_activity():
    """Create a new activity record"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['curator_id', 'server_id', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate curator and server exist
        curator = Curator.query.get(data['curator_id'])
        if not curator:
            return jsonify({'error': 'Curator not found'}), 404
        
        server = DiscordServer.query.get(data['server_id'])
        if not server:
            return jsonify({'error': 'Server not found'}), 404
        
        # Calculate points based on activity type
        activity_type = data['type']
        points = Config.RATING_POINTS.get(activity_type, 0)
        
        # Create activity
        activity = Activity()
        activity.curator_id = data['curator_id']
        activity.server_id = data['server_id']
        activity.type = activity_type
        activity.content = data.get('content')
        activity.points = points
        activity.message_id = data.get('message_id')
        activity.channel_id = data.get('channel_id')
        activity.timestamp = datetime.utcnow()
        
        db.session.add(activity)
        
        # Update curator's total points
        curator.total_points += points
        
        # Recalculate curator rating
        from utils.rating import calculate_curator_rating
        rating_data = calculate_curator_rating(curator.id)
        curator.rating_level = rating_data['level']
        
        db.session.commit()
        
        return jsonify(activity.to_dict()), 201
        
    except Exception as e:
        logging.error(f"Error creating activity: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create activity'}), 500

@activities_bp.route('/stats', methods=['GET'])
def get_activity_stats():
    """Get comprehensive activity statistics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Overall statistics
        total_activities = Activity.query.filter(Activity.timestamp >= cutoff_date).count()
        
        # Activity type breakdown
        type_stats = db.session.query(
            Activity.type,
            func.count(Activity.id).label('count'),
            func.sum(Activity.points).label('total_points')
        ).filter(
            Activity.timestamp >= cutoff_date
        ).group_by(Activity.type).all()
        
        type_breakdown = {}
        for stat in type_stats:
            type_breakdown[stat.type] = {
                'count': stat.count,
                'total_points': stat.total_points or 0
            }
        
        # Top active curators
        curator_stats = db.session.query(
            Activity.curator_id,
            func.count(Activity.id).label('activity_count'),
            func.sum(Activity.points).label('total_points')
        ).filter(
            Activity.timestamp >= cutoff_date
        ).group_by(Activity.curator_id).order_by(
            func.sum(Activity.points).desc()
        ).limit(10).all()
        
        top_curators = []
        for stat in curator_stats:
            curator = Curator.query.get(stat.curator_id)
            if curator:
                top_curators.append({
                    'curator_id': curator.id,
                    'curator_name': curator.name,
                    'activity_count': stat.activity_count,
                    'total_points': stat.total_points or 0
                })
        
        # Server activity breakdown
        server_stats = db.session.query(
            Activity.server_id,
            func.count(Activity.id).label('activity_count')
        ).filter(
            Activity.timestamp >= cutoff_date
        ).group_by(Activity.server_id).all()
        
        server_breakdown = []
        for stat in server_stats:
            server = DiscordServer.query.get(stat.server_id)
            if server:
                server_breakdown.append({
                    'server_id': server.id,
                    'server_name': server.name,
                    'activity_count': stat.activity_count
                })
        
        stats_data = {
            'total_activities': total_activities,
            'type_breakdown': type_breakdown,
            'top_curators': top_curators,
            'server_breakdown': server_breakdown,
            'period_days': days
        }
        
        return jsonify(stats_data)
        
    except Exception as e:
        logging.error(f"Error getting activity stats: {e}")
        return jsonify({'error': 'Failed to fetch activity statistics'}), 500

@activities_bp.route('/export', methods=['GET'])
def export_activities():
    """Export activities as CSV or JSON"""
    try:
        format_type = request.args.get('format', 'json')
        days = request.args.get('days', 30, type=int)
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        activities = Activity.query.filter(Activity.timestamp >= cutoff_date).order_by(Activity.timestamp.desc()).all()
        
        if format_type.lower() == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['ID', 'Curator Name', 'Server Name', 'Type', 'Content', 'Points', 'Timestamp'])
            
            # Write data
            for activity in activities:
                writer.writerow([
                    activity.id,
                    activity.curator.name if activity.curator else '',
                    activity.discord_server.name if activity.discord_server else '',
                    activity.type,
                    activity.content or '',
                    activity.points,
                    activity.timestamp.isoformat()
                ])
            
            output.seek(0)
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=activities_{days}days.csv'
            }
        
        else:
            # JSON format
            activities_data = [activity.to_dict() for activity in activities]
            return jsonify(activities_data)
        
    except Exception as e:
        logging.error(f"Error exporting activities: {e}")
        return jsonify({'error': 'Failed to export activities'}), 500
