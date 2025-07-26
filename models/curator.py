# GovTracker2 Python Migration by Replit Agent
from database import db
from sqlalchemy import Column, Integer, String, JSON, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime

class Curator(db.Model):
    __tablename__ = 'curators'
    
    # MySQL compatible AUTO_INCREMENT primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # JSON field compatible with MySQL 5.7+
    factions = Column(JSON, nullable=True)
    
    curator_type = Column(String(100), nullable=True)
    subdivision = Column(String(255), nullable=True)
    
    # Rating and statistics
    total_points = Column(Integer, default=0)
    rating_level = Column(String(50), default='Ужасно')
    
    # Timestamps using DATETIME for MySQL compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    activities = db.relationship('Activity', backref='curator', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Curator {self.name} ({self.discord_id})>'
    
    def to_dict(self):
        """Convert curator to dictionary for JSON responses"""
        return {
            'id': self.id,
            'discord_id': self.discord_id,
            'name': self.name,
            'factions': self.factions or [],
            'curator_type': self.curator_type,
            'subdivision': self.subdivision,
            'total_points': self.total_points,
            'rating_level': self.rating_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_activity_stats(self, days=30):
        """Get activity statistics for the curator"""
        from models.activity import Activity
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        activities = Activity.query.filter(
            Activity.curator_id == self.id,
            Activity.timestamp >= cutoff_date
        ).all()
        
        stats = {
            'total_activities': len(activities),
            'messages': len([a for a in activities if a.type == 'message']),
            'reactions': len([a for a in activities if a.type == 'reaction']),
            'replies': len([a for a in activities if a.type == 'reply']),
            'task_verifications': len([a for a in activities if a.type == 'task_verification'])
        }
        
        return stats
    
    @classmethod
    def find_by_discord_id(cls, discord_id):
        """Find curator by Discord ID"""
        return cls.query.filter_by(discord_id=str(discord_id)).first()
    
    @classmethod
    def get_top_curators(cls, limit=10):
        """Get top curators by total points"""
        return cls.query.order_by(cls.total_points.desc()).limit(limit).all()
