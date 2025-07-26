# GovTracker2 Python Migration by Replit Agent
from flask import Blueprint, jsonify, current_app
from app import db
import logging

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        with current_app.app_context():
            from models.curator import Curator
            from models.activity import Activity
            from models.discord_server import DiscordServer
            from models.response_tracking import ResponseTracking
            
            # Basic counts
            total_curators = Curator.query.count()
            active_servers = DiscordServer.query.filter_by(is_active=True).count()
            total_activities = Activity.query.count()
            
            # Average response time (default to 0 if no data)
            try:
                average_response_time = ResponseTracking.get_average_response_time(days=30)
            except:
                average_response_time = 0
            
            # Top curators by points
            try:
                top_curators = Curator.get_top_curators(limit=10)
                top_curators_data = [
                    {
                        'id': curator.id,
                        'name': curator.name,
                        'total_points': curator.total_points,
                        'rating_level': curator.rating_level,
                        'discord_id': curator.discord_id
                    }
                    for curator in top_curators
                ]
            except:
                top_curators_data = []
            
            # Daily statistics for the last 30 days
            try:
                daily_stats = Activity.get_daily_stats(days=30)
            except:
                daily_stats = []
            
            # Recent activities
            try:
                recent_activities = Activity.get_recent_activities(limit=10)
                recent_activities_data = [activity.to_dict() for activity in recent_activities]
            except:
                recent_activities_data = []
            
            # Response time distribution
            try:
                response_distribution = ResponseTracking.get_response_time_distribution(days=30)
            except:
                response_distribution = {}
            
            # Rating distribution
            try:
                from utils.rating import get_rating_distribution
                rating_distribution = get_rating_distribution()
            except:
                rating_distribution = {}
            
            # Server statistics
            try:
                server_stats = DiscordServer.get_server_stats()
            except:
                server_stats = {}
            
            dashboard_data = {
                'totalCurators': total_curators,
                'activeServers': active_servers,
                'totalActivities': total_activities,
                'averageResponseTime': average_response_time,
                'topCurators': top_curators_data,
                'dailyStats': daily_stats,
                'recentActivities': recent_activities_data,
                'responseDistribution': response_distribution,
                'ratingDistribution': rating_distribution,
                'serverStats': server_stats
            }
            
            return jsonify(dashboard_data)
        
    except Exception as e:
        logging.error(f"Error getting dashboard stats: {e}")
        return jsonify({'error': 'Failed to fetch dashboard statistics'}), 500

@dashboard_bp.route('/activity-summary', methods=['GET'])
def get_activity_summary():
    """Get activity summary for charts"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # Last 7 days activity summary
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        from app import db
        
        activity_summary = db.session.query(
            func.date(Activity.timestamp).label('date'),
            Activity.type,
            func.count(Activity.id).label('count')
        ).filter(
            Activity.timestamp >= cutoff_date
        ).group_by(
            func.date(Activity.timestamp),
            Activity.type
        ).all()
        
        # Format for frontend charts
        summary_data = {}
        for item in activity_summary:
            date_str = str(item.date)
            if date_str not in summary_data:
                summary_data[date_str] = {
                    'date': date_str,
                    'message': 0,
                    'reaction': 0,
                    'reply': 0,
                    'task_verification': 0
                }
            summary_data[date_str][item.type] = item.count
        
        return jsonify(list(summary_data.values()))
        
    except Exception as e:
        logging.error(f"Error getting activity summary: {e}")
        return jsonify({'error': 'Failed to fetch activity summary'}), 500

@dashboard_bp.route('/performance-metrics', methods=['GET'])
def get_performance_metrics():
    """Get performance metrics for dashboard"""
    try:
        from datetime import datetime, timedelta
        
        # Performance metrics for the last 30 days
        metrics = {
            'curator_performance': [],
            'server_performance': [],
            'response_times': [],
            'activity_trends': []
        }
        
        # Top performing curators
        curators = Curator.query.order_by(Curator.total_points.desc()).limit(5).all()
        for curator in curators:
            stats = curator.get_activity_stats(days=30)
            response_stats = ResponseTracking.get_curator_response_stats(curator.id, days=30)
            
            metrics['curator_performance'].append({
                'name': curator.name,
                'points': curator.total_points,
                'activities': stats['total_activities'],
                'avg_response_time': response_stats['average_time']
            })
        
        # Server activity levels
        servers = DiscordServer.get_active_servers()
        for server in servers:
            activity_count = server.get_activity_count(days=30)
            metrics['server_performance'].append({
                'name': server.name,
                'activity_count': activity_count,
                'active_curators': len(server.get_active_curators())
            })
        
        return jsonify(metrics)
        
    except Exception as e:
        logging.error(f"Error getting performance metrics: {e}")
        return jsonify({'error': 'Failed to fetch performance metrics'}), 500
