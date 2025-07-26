# GovTracker2 Python Migration by Replit Agent
from datetime import datetime, timedelta
from models.response_tracking import ResponseTracking
from config import Config
import logging

def calculate_response_metrics(server_id=None, curator_id=None, days=30):
    """Calculate comprehensive response time metrics"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = ResponseTracking.query.filter(
            ResponseTracking.mention_timestamp >= cutoff_date
        )
        
        if server_id:
            query = query.filter_by(server_id=server_id)
        
        if curator_id:
            query = query.filter_by(curator_id=curator_id)
        
        responses = query.all()
        
        if not responses:
            return {
                'total_responses': 0,
                'average_time': 0,
                'median_time': 0,
                'fastest_time': 0,
                'slowest_time': 0,
                'quality_distribution': {'good': 0, 'average': 0, 'poor': 0},
                'hourly_distribution': {},
                'daily_trend': []
            }
        
        # Basic statistics
        times = [r.response_time_seconds for r in responses]
        times.sort()
        
        total_responses = len(responses)
        average_time = sum(times) // total_responses
        median_time = times[total_responses // 2]
        fastest_time = min(times)
        slowest_time = max(times)
        
        # Quality distribution
        quality_distribution = {
            'good': sum(1 for t in times if t <= Config.RESPONSE_TIME_GOOD),
            'poor': sum(1 for t in times if t >= Config.RESPONSE_TIME_POOR),
            'average': 0
        }
        quality_distribution['average'] = total_responses - quality_distribution['good'] - quality_distribution['poor']
        
        # Hourly distribution
        hourly_distribution = {}
        for response in responses:
            hour = response.mention_timestamp.hour
            if hour not in hourly_distribution:
                hourly_distribution[hour] = {'count': 0, 'avg_time': 0}
            hourly_distribution[hour]['count'] += 1
        
        # Calculate average time per hour
        for hour in hourly_distribution:
            hour_responses = [r for r in responses if r.mention_timestamp.hour == hour]
            hour_times = [r.response_time_seconds for r in hour_responses]
            hourly_distribution[hour]['avg_time'] = sum(hour_times) // len(hour_times)
        
        # Daily trend (last 7 days)
        daily_trend = []
        for i in range(7):
            day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_responses = [r for r in responses if day_start <= r.mention_timestamp < day_end]
            day_count = len(day_responses)
            day_avg = sum(r.response_time_seconds for r in day_responses) // day_count if day_count > 0 else 0
            
            daily_trend.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'count': day_count,
                'avg_time': day_avg
            })
        
        daily_trend.reverse()  # Most recent first
        
        return {
            'total_responses': total_responses,
            'average_time': average_time,
            'median_time': median_time,
            'fastest_time': fastest_time,
            'slowest_time': slowest_time,
            'quality_distribution': quality_distribution,
            'hourly_distribution': hourly_distribution,
            'daily_trend': daily_trend
        }
        
    except Exception as e:
        logging.error(f"Error calculating response metrics: {e}")
        return {
            'total_responses': 0,
            'average_time': 0,
            'error': str(e)
        }

def get_response_quality(response_time_seconds):
    """Determine response quality based on time"""
    if response_time_seconds <= Config.RESPONSE_TIME_GOOD:
        return {
            'quality': 'good',
            'color': 'green',
            'description': 'Excellent response time',
            'score': 100
        }
    elif response_time_seconds >= Config.RESPONSE_TIME_POOR:
        return {
            'quality': 'poor',
            'color': 'red',
            'description': 'Slow response time',
            'score': 30
        }
    else:
        # Calculate score based on linear scale between good and poor thresholds
        good_threshold = Config.RESPONSE_TIME_GOOD
        poor_threshold = Config.RESPONSE_TIME_POOR
        
        # Linear interpolation between 100 (good) and 30 (poor)
        score_range = 70  # 100 - 30
        time_range = poor_threshold - good_threshold
        time_offset = response_time_seconds - good_threshold
        
        score = 100 - (time_offset / time_range * score_range)
        score = max(30, min(100, int(score)))
        
        return {
            'quality': 'average',
            'color': 'orange',
            'description': 'Average response time',
            'score': score
        }

def analyze_response_patterns(curator_id, days=30):
    """Analyze response patterns for a specific curator"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        responses = ResponseTracking.query.filter(
            ResponseTracking.curator_id == curator_id,
            ResponseTracking.mention_timestamp >= cutoff_date
        ).all()
        
        if not responses:
            return {
                'patterns': [],
                'recommendations': [],
                'peak_hours': [],
                'consistency_score': 0
            }
        
        patterns = []
        recommendations = []
        
        # Analyze by day of week
        day_stats = {}
        for response in responses:
            day = response.mention_timestamp.strftime('%A')
            if day not in day_stats:
                day_stats[day] = []
            day_stats[day].append(response.response_time_seconds)
        
        # Find best and worst days
        day_averages = {}
        for day, times in day_stats.items():
            day_averages[day] = sum(times) // len(times)
        
        if day_averages:
            best_day = min(day_averages, key=day_averages.get)
            worst_day = max(day_averages, key=day_averages.get)
            
            patterns.append(f"Best performance on {best_day} ({day_averages[best_day]}s avg)")
            patterns.append(f"Slowest on {worst_day} ({day_averages[worst_day]}s avg)")
        
        # Analyze by hour
        hour_stats = {}
        for response in responses:
            hour = response.mention_timestamp.hour
            if hour not in hour_stats:
                hour_stats[hour] = []
            hour_stats[hour].append(response.response_time_seconds)
        
        # Find peak performance hours
        hour_averages = {}
        for hour, times in hour_stats.items():
            if len(times) >= 3:  # Only consider hours with at least 3 responses
                hour_averages[hour] = sum(times) // len(times)
        
        peak_hours = []
        if hour_averages:
            # Sort hours by performance (fastest first)
            sorted_hours = sorted(hour_averages.items(), key=lambda x: x[1])
            peak_hours = [f"{hour:02d}:00" for hour, _ in sorted_hours[:3]]
        
        # Calculate consistency score
        if len(responses) >= 5:
            times = [r.response_time_seconds for r in responses]
            avg_time = sum(times) / len(times)
            variance = sum((t - avg_time) ** 2 for t in times) / len(times)
            std_dev = variance ** 0.5
            
            # Lower standard deviation = higher consistency
            # Normalize to 0-100 scale
            consistency_score = max(0, min(100, int(100 - (std_dev / avg_time * 100))))
        else:
            consistency_score = 0
        
        # Generate recommendations
        if len(responses) >= 10:
            recent_responses = sorted(responses, key=lambda x: x.mention_timestamp)[-5:]
            recent_avg = sum(r.response_time_seconds for r in recent_responses) / len(recent_responses)
            overall_avg = sum(r.response_time_seconds for r in responses) / len(responses)
            
            if recent_avg > overall_avg * 1.2:
                recommendations.append("Recent performance has declined. Consider reviewing your response strategy.")
            elif recent_avg < overall_avg * 0.8:
                recommendations.append("Great improvement in recent performance! Keep it up!")
        
        if consistency_score < 50:
            recommendations.append("Try to maintain more consistent response times.")
        
        if hour_averages:
            fastest_hour = min(hour_averages, key=hour_averages.get)
            recommendations.append(f"You perform best at {fastest_hour:02d}:00. Try to be more active during this time.")
        
        return {
            'patterns': patterns,
            'recommendations': recommendations,
            'peak_hours': peak_hours,
            'consistency_score': consistency_score,
            'day_averages': day_averages,
            'hour_averages': hour_averages
        }
        
    except Exception as e:
        logging.error(f"Error analyzing response patterns: {e}")
        return {
            'patterns': [],
            'recommendations': [],
            'peak_hours': [],
            'consistency_score': 0
        }

def get_server_response_comparison(days=30):
    """Compare response times across all servers"""
    try:
        from models.discord_server import DiscordServer
        
        servers = DiscordServer.get_active_servers()
        comparison_data = []
        
        for server in servers:
            metrics = calculate_response_metrics(server_id=server.id, days=days)
            
            comparison_data.append({
                'server_id': server.id,
                'server_name': server.name,
                'total_responses': metrics['total_responses'],
                'average_time': metrics['average_time'],
                'quality_distribution': metrics['quality_distribution']
            })
        
        # Sort by average response time
        comparison_data.sort(key=lambda x: x['average_time'])
        
        return comparison_data
        
    except Exception as e:
        logging.error(f"Error getting server response comparison: {e}")
        return []
