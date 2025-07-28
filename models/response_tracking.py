# GovTracker2 Python Migration by Replit Agent
from app import db
from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from datetime import datetime

class ResponseTracking(db.Model):
    __tablename__ = 'response_tracking'
    
    # MySQL compatible AUTO_INCREMENT primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Curator who responded
    curator_id = Column(Integer, ForeignKey('curators.id'), nullable=False, index=True)
    
    # Server where the response occurred
    server_id = Column(Integer, ForeignKey('discord_servers.id'), nullable=False, index=True)
    
    # Timing information using DATETIME for MySQL compatibility
    mention_timestamp = Column(DateTime, nullable=False, index=True)
    response_timestamp = Column(DateTime, nullable=False)
    response_time_seconds = Column(Integer, nullable=False, index=True)
    
    # Message details
    mention_message_id = Column(String(255), nullable=True)
    response_message_id = Column(String(255), nullable=True)
    channel_id = Column(String(255), nullable=True)
    
    # Keywords that triggered the tracking
    trigger_keywords = Column(String(500), nullable=True)  # comma-separated keywords
    
    def __repr__(self):
        return f'<ResponseTracking {self.response_time_seconds}s by curator {self.curator_id}>'
    
    def to_dict(self):
        """Convert response tracking to dictionary for JSON responses"""
        return {
            'id': self.id,
            'curator_id': self.curator_id,
            'server_id': self.server_id,
            'mention_timestamp': self.mention_timestamp.isoformat() if self.mention_timestamp else None,
            'response_timestamp': self.response_timestamp.isoformat() if self.response_timestamp else None,
            'response_time_seconds': self.response_time_seconds,
            'mention_message_id': self.mention_message_id,
            'response_message_id': self.response_message_id,
            'channel_id': self.channel_id,
            'trigger_keywords': self.trigger_keywords.split(',') if self.trigger_keywords else [],
            'curator_name': self.curator.name if self.curator else None,
            'server_name': self.discord_server.name if self.discord_server else None,
            'response_quality': self.get_response_quality()
        }
    
    def get_response_quality(self):
        """Determine response quality based on time"""
        from config import Config
        
        if self.response_time_seconds <= Config.RESPONSE_TIME_GOOD:
            return 'good'
        elif self.response_time_seconds >= Config.RESPONSE_TIME_POOR:
            return 'poor'
        else:
            return 'average'
    
    @classmethod
    def get_average_response_time(cls, curator_id=None, server_id=None, days=30):
        """Calculate average response time"""
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        query = cls.query
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(cls.mention_timestamp >= cutoff_date)
        
        if curator_id:
            query = query.filter_by(curator_id=curator_id)
        
        if server_id:
            query = query.filter_by(server_id=server_id)
        
        result = query.with_entities(func.avg(cls.response_time_seconds)).scalar()
        return int(result) if result else 0
    
    @classmethod
    def get_response_time_distribution(cls, days=30):
        """Get response time distribution for analytics"""
        from datetime import datetime, timedelta
        from config import Config
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        responses = cls.query.filter(cls.mention_timestamp >= cutoff_date).all()
        
        distribution = {
            'good': 0,    # <= 60 seconds
            'average': 0, # 61-299 seconds
            'poor': 0     # >= 300 seconds
        }
        
        for response in responses:
            time_seconds = response.response_time_seconds
            if time_seconds <= Config.RESPONSE_TIME_GOOD:
                distribution['good'] += 1
            elif time_seconds >= Config.RESPONSE_TIME_POOR:
                distribution['poor'] += 1
            else:
                distribution['average'] += 1
        
        return distribution
    
    @classmethod
    def get_curator_response_stats(cls, curator_id, days=30):
        """Get response statistics for a specific curator"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        responses = cls.query.filter(
            cls.curator_id == curator_id,
            cls.mention_timestamp >= cutoff_date
        ).all()
        
        if not responses:
            return {
                'total_responses': 0,
                'average_time': 0,
                'fastest_time': 0,
                'slowest_time': 0,
                'good_responses': 0,
                'poor_responses': 0
            }
        
        times = [r.response_time_seconds for r in responses]
        
        return {
            'total_responses': len(responses),
            'average_time': sum(times) // len(times),
            'fastest_time': min(times),
            'slowest_time': max(times),
            'good_responses': sum(1 for t in times if t <= 60),
            'poor_responses': sum(1 for t in times if t >= 300)
        }
