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
    role_tag_id = Column(String(255), nullable=True)  # Role ID for notifications
    
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
            'role_tag_id': self.role_tag_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'activity_count': self.get_activity_count()
        }
    
    def get_activity_count(self, days=30):
        """Get activity count for this server"""
        from models.activity import Activity
        from datetime import datetime, timedelta
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return Activity.query.filter(
                Activity.server_id == self.id,
                Activity.timestamp >= cutoff_date
            ).count()
        else:
            return Activity.query.filter_by(server_id=self.id).count()
    
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
