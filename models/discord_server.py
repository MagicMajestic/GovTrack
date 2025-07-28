# GovTracker2 Python Migration by Replit Agent
from database import db
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

class DiscordServer(db.Model):
    __tablename__ = 'discord_servers'
    
    # MySQL compatible AUTO_INCREMENT primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Discord server details
    server_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Curator and notification settings
    curator_role_id = Column(String(255), nullable=True)  # ID роли куратора
    notification_channel_id = Column(String(255), nullable=True)  # Канал для уведомлений
    tasks_channel_id = Column(String(255), nullable=True)  # Канал с тасками
    
    # Server status
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps using DATETIME for MySQL compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    activities = db.relationship('Activity', backref='discord_server', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<DiscordServer {self.name} ({self.server_id})>'
    
    def to_dict(self):
        """Convert server to dictionary for JSON responses"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'name': self.name,
            'curator_role_id': self.curator_role_id,
            'notification_channel_id': self.notification_channel_id,
            'tasks_channel_id': self.tasks_channel_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'activity_count': self.get_activity_count(),
            'curator_count': self.get_curator_count(),
            'avg_response_time': self.get_average_response_time(),
            'reactions_count': self.get_reactions_count()
        }

    def get_curator_count(self):
        """Get number of curators assigned to this server"""
        try:
            from models.activity import Activity
            from sqlalchemy import func
            
            # Count distinct curators with activities on this server
            with db.session.no_autoflush:
                count = db.session.query(func.count(Activity.curator_id.distinct())).filter(
                    Activity.server_id == self.id
                ).scalar()
                
                return count if count is not None else 0
        except Exception as e:
            return 0

    def get_average_response_time(self, days=30):
        """Get average response time for this server"""
        try:
            from models.response_tracking import ResponseTracking
            from sqlalchemy import func
            from datetime import datetime, timedelta
            
            with db.session.no_autoflush:
                since = datetime.utcnow() - timedelta(days=days)
                result = db.session.query(func.avg(ResponseTracking.response_time)).filter(
                    ResponseTracking.server_id == self.id,
                    ResponseTracking.created_at >= since,
                    ResponseTracking.response_time.isnot(None)
                ).scalar()
                
                return int(result) if result else 0
        except:
            return 0

    def get_reactions_count(self, days=30):
        """Get total reactions count for this server"""
        try:
            from models.activity import Activity
            from datetime import datetime, timedelta
            
            with db.session.no_autoflush:
                since = datetime.utcnow() - timedelta(days=days)
                return Activity.query.filter(
                    Activity.server_id == self.id,
                    Activity.type == 'reaction',
                    Activity.timestamp >= since
                ).count()
        except:
            return 0
    
    def get_activity_count(self, days=30):
        """Get activity count for this server"""
        try:
            from models.activity import Activity
            from datetime import datetime, timedelta
            
            with db.session.no_autoflush:
                if days:
                    cutoff_date = datetime.utcnow() - timedelta(days=days)
                    return Activity.query.filter(
                        Activity.server_id == self.id,
                        Activity.timestamp >= cutoff_date
                    ).count()
                else:
                    return Activity.query.filter_by(server_id=self.id).count()
        except:
            return 0
    
    def get_active_curators(self):
        """Get curators active on this server"""
        from models.activity import Activity
        from models.curator import Curator
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        curator_ids = db.session.query(Activity.curator_id.distinct()).filter(
            Activity.server_id == self.id,
            Activity.timestamp >= cutoff_date
        ).all()
        
        curator_ids = [cid[0] for cid in curator_ids]
        return Curator.query.filter(Curator.id.in_(curator_ids)).all()
    
    @classmethod
    def find_by_server_id(cls, server_id):
        """Find server by Discord server ID"""
        return cls.query.filter_by(server_id=str(server_id)).first()
    
    @classmethod
    def get_active_servers(cls):
        """Get all active servers"""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_server_stats(cls):
        """Get overall server statistics"""
        total_servers = cls.query.count()
        active_servers = cls.query.filter_by(is_active=True).count()
        
        return {
            'total_servers': total_servers,
            'active_servers': active_servers,
            'inactive_servers': total_servers - active_servers
        }
