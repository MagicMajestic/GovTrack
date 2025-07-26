# GovTracker2 Python Migration by Replit Agent
from datetime import datetime, timedelta
from models.curator import Curator
from models.activity import Activity
from models.response_tracking import ResponseTracking
from config import Config
from database import db
import logging

def calculate_curator_rating(curator_id, days=30):
    """Calculate comprehensive rating for a curator"""
    try:
        curator = Curator.query.get(curator_id)
        if not curator:
            return {'total_points': 0, 'level': 'Ужасно', 'breakdown': {}}
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get activities in the specified period
        activities = Activity.query.filter(
            Activity.curator_id == curator_id,
            Activity.timestamp >= cutoff_date
        ).all()
        
        # Calculate points breakdown
        breakdown = {
            'messages': 0,
            'reactions': 0,
            'replies': 0,
            'task_verifications': 0,
            'total_activities': len(activities)
        }
        
        total_points = 0
        
        for activity in activities:
            activity_type = activity.type
            points = activity.points
            total_points += points
            
            if activity_type == 'message':
                breakdown['messages'] += points
            elif activity_type == 'reaction':
                breakdown['reactions'] += points
            elif activity_type == 'reply':
                breakdown['replies'] += points
            elif activity_type == 'task_verification':
                breakdown['task_verifications'] += points
        
        # Calculate response time bonus/penalty
        response_stats = ResponseTracking.get_curator_response_stats(curator_id, days)
        response_bonus = calculate_response_bonus(response_stats)
        
        # Apply response time modifier
        final_points = total_points + response_bonus
        
        # Determine rating level
        level = determine_rating_level(final_points)
        
        return {
            'total_points': final_points,
            'base_points': total_points,
            'response_bonus': response_bonus,
            'level': level,
            'breakdown': breakdown,
            'response_stats': response_stats
        }
        
    except Exception as e:
        logging.error(f"Error calculating curator rating: {e}")
        return {'total_points': 0, 'level': 'Ужасно', 'breakdown': {}}

def calculate_response_bonus(response_stats):
    """Calculate bonus/penalty based on response times"""
    if response_stats['total_responses'] == 0:
        return 0
    
    good_responses = response_stats['good_responses']
    poor_responses = response_stats['poor_responses']
    total_responses = response_stats['total_responses']
    
    # Calculate bonus: +1 point per good response, -1 point per poor response
    bonus = good_responses - poor_responses
    
    # Apply percentage-based modifier
    good_percentage = good_responses / total_responses
    poor_percentage = poor_responses / total_responses
    
    if good_percentage >= 0.8:  # 80% or more good responses
        bonus += int(total_responses * 0.2)  # 20% bonus
    elif poor_percentage >= 0.5:  # 50% or more poor responses
        bonus -= int(total_responses * 0.3)  # 30% penalty
    
    return max(bonus, -total_responses)  # Don't penalty more than total responses

def determine_rating_level(points):
    """Determine rating level based on points"""
    levels = Config.RATING_LEVELS
    
    if points >= levels['excellent']:
        return 'Великолепно'
    elif points >= levels['good']:
        return 'Хорошо'
    elif points >= levels['normal']:
        return 'Нормально'
    elif points >= levels['poor']:
        return 'Плохо'
    else:
        return 'Ужасно'

def get_rating_distribution():
    """Get distribution of curator ratings"""
    try:
        curators = Curator.query.all()
        distribution = {
            'Великолепно': 0,
            'Хорошо': 0,
            'Нормально': 0,
            'Плохо': 0,
            'Ужасно': 0
        }
        
        for curator in curators:
            level = curator.rating_level or 'Ужасно'
            if level in distribution:
                distribution[level] += 1
            else:
                distribution['Ужасно'] += 1
        
        return distribution
        
    except Exception as e:
        logging.error(f"Error getting rating distribution: {e}")
        return {'Ужасно': 0}

def update_all_ratings():
    """Update ratings for all curators"""
    try:
        curators = Curator.query.all()
        updated_count = 0
        
        for curator in curators:
            rating_data = calculate_curator_rating(curator.id)
            curator.total_points = rating_data['total_points']
            curator.rating_level = rating_data['level']
            updated_count += 1
        
        db.session.commit()
        logging.info(f"Updated ratings for {updated_count} curators")
        
        return {
            'success': True,
            'updated_count': updated_count
        }
        
    except Exception as e:
        logging.error(f"Error updating all ratings: {e}")
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }

def get_curator_ranking(curator_id):
    """Get curator's rank among all curators"""
    try:
        curator = Curator.query.get(curator_id)
        if not curator:
            return None
        
        # Count curators with higher points
        higher_count = Curator.query.filter(
            Curator.total_points > curator.total_points
        ).count()
        
        rank = higher_count + 1
        total_curators = Curator.query.count()
        
        return {
            'rank': rank,
            'total_curators': total_curators,
            'percentile': round((1 - (rank - 1) / total_curators) * 100, 1) if total_curators > 0 else 0
        }
        
    except Exception as e:
        logging.error(f"Error getting curator ranking: {e}")
        return None

def calculate_weekly_improvement(curator_id):
    """Calculate curator's improvement over the last week"""
    try:
        # Get current week points
        current_week_data = calculate_curator_rating(curator_id, days=7)
        current_points = current_week_data['total_points']
        
        # Get previous week points
        previous_week_start = datetime.utcnow() - timedelta(days=14)
        previous_week_end = datetime.utcnow() - timedelta(days=7)
        
        previous_activities = Activity.query.filter(
            Activity.curator_id == curator_id,
            Activity.timestamp >= previous_week_start,
            Activity.timestamp < previous_week_end
        ).all()
        
        previous_points = sum(activity.points for activity in previous_activities)
        
        # Calculate improvement
        improvement = current_points - previous_points
        improvement_percentage = 0
        if previous_points > 0:
            improvement_percentage = round((improvement / previous_points) * 100, 1)
        
        return {
            'current_week_points': current_points,
            'previous_week_points': previous_points,
            'improvement': improvement,
            'improvement_percentage': improvement_percentage,
            'trend': 'up' if improvement > 0 else 'down' if improvement < 0 else 'stable'
        }
        
    except Exception as e:
        logging.error(f"Error calculating weekly improvement: {e}")
        return None

def get_activity_insights(curator_id, days=30):
    """Get insights about curator's activity patterns"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        activities = Activity.query.filter(
            Activity.curator_id == curator_id,
            Activity.timestamp >= cutoff_date
        ).all()
        
        if not activities:
            return {'insights': [], 'recommendations': []}
        
        # Analyze activity patterns
        insights = []
        recommendations = []
        
        # Activity type analysis
        type_counts = {}
        for activity in activities:
            type_counts[activity.type] = type_counts.get(activity.type, 0) + 1
        
        most_common = max(type_counts, key=type_counts.get) if type_counts else None
        least_common = min(type_counts, key=type_counts.get) if type_counts else None
        
        if most_common:
            insights.append(f"Most active in: {most_common} ({type_counts[most_common]} activities)")
        
        if least_common and type_counts[least_common] < type_counts[most_common] * 0.3:
            recommendations.append(f"Consider increasing {least_common} activities for better balance")
        
        # Response time analysis
        response_stats = ResponseTracking.get_curator_response_stats(curator_id, days)
        if response_stats['total_responses'] > 0:
            avg_time = response_stats['average_time']
            if avg_time <= Config.RESPONSE_TIME_GOOD:
                insights.append(f"Excellent response time: {avg_time}s average")
            elif avg_time >= Config.RESPONSE_TIME_POOR:
                recommendations.append("Try to respond faster to help requests")
        
        # Activity frequency analysis
        daily_avg = len(activities) / days
        if daily_avg >= 5:
            insights.append("Highly active curator")
        elif daily_avg < 1:
            recommendations.append("Consider increasing daily activity")
        
        return {
            'insights': insights,
            'recommendations': recommendations,
            'activity_distribution': type_counts,
            'daily_average': round(daily_avg, 1)
        }
        
    except Exception as e:
        logging.error(f"Error getting activity insights: {e}")
        return {'insights': [], 'recommendations': []}
