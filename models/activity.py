# GovTracker2 Python Migration by Replit Agent
from app import db
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime

class Activity(db.Model):
    __tablename__ = 'activities'
    
    # MySQL compatible AUTO_INCREMENT primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    curator_id = Column(Integer, ForeignKey('curators.id'), nullable=False, index=True)
    server_id = Column(Integer, ForeignKey('discord_servers.id'), nullable=False, index=True)
    
    # Activity details
    type = Column(String(100), nullable=False, index=True)  # message, reaction, reply, task_verification
    content = Column(Text, nullable=True)
    
    # Points earned for this activity
    points = Column(Integer, default=0)
    
    # Timestamp using DATETIME for MySQL compatibility
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Additional metadata
    message_id = Column(String(255), nullable=True)
    channel_id = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f'<Activity {self.type} by curator {self.curator_id} at {self.timestamp}>'
    
    def to_dict(self):
        """Convert activity to dictionary for JSON responses"""
        return {
            'id': self.id,
            'curator_id': self.curator_id,
            'server_id': self.server_id,
            'type': self.type,
            'content': self.content,
            'points': self.points,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'message_id': self.message_id,
            'channel_id': self.channel_id,
            'curator_name': self.curator.name if self.curator else None,
            'server_name': self.discord_server.name if self.discord_server else None
        }
    
    @classmethod
    def get_recent_activities(cls, limit=50):
        """Get recent activities"""
        return cls.query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_daily_stats(cls, days=30):
        """Get daily activity statistics"""
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Group activities by date
        daily_stats = db.session.query(
            func.date(cls.timestamp).label('date'),
            func.count(cls.id).label('count'),
            cls.type
        ).filter(
            cls.timestamp >= cutoff_date
        ).group_by(
            func.date(cls.timestamp),
            cls.type
        ).all()
        
        # Format results for frontend consumption
        result = {}
        for stat in daily_stats:
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
        
        return list(result.values())
    
    @classmethod
    def get_activity_by_server(cls, server_id, limit=100):
        """Get activities for a specific server"""
        return cls.query.filter_by(server_id=server_id).order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_activity_by_curator(cls, curator_id, limit=100):
        """Get activities for a specific curator"""
        return cls.query.filter_by(curator_id=curator_id).order_by(cls.timestamp.desc()).limit(limit).all()
