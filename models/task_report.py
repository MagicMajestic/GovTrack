# GovTracker2 Python Migration by Replit Agent
from app import db
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

class TaskReport(db.Model):
    __tablename__ = 'task_reports'
    
    # MySQL compatible AUTO_INCREMENT primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Discord information
    discord_user_id = Column(String(255), nullable=False, index=True)  # Discord ID of report author
    discord_username = Column(String(255), nullable=False)
    discord_server_id = Column(String(255), nullable=False)  # Server where task was reported
    discord_channel_id = Column(String(255), nullable=False)  # Channel where task was reported
    discord_message_id = Column(String(255), nullable=False)  # Original message ID
    
    # Task details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Review information
    reviewer_name = Column(String(255), nullable=True)
    review_started_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Status using VARCHAR for MySQL compatibility
    status = Column(String(50), default='pending')  # pending, in_review, completed, archived
    
    # Timestamps using DATETIME for MySQL compatibility
    report_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TaskReport {self.title} by {self.discord_username}>'
    
    def to_dict(self):
        """Convert task report to dictionary for JSON responses"""
        return {
            'id': self.id,
            'discord_user_id': self.discord_user_id,
            'discord_username': self.discord_username,
            'discord_server_id': self.discord_server_id,
            'discord_channel_id': self.discord_channel_id,
            'discord_message_id': self.discord_message_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'status_display': self.get_status_display(),
            'reviewer_name': self.reviewer_name,
            'review_started_at': self.review_started_at.isoformat() if self.review_started_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    

    
    def update_status(self, new_status, reviewer_name=None):
        """Update report status with validation"""
        valid_statuses = ['pending', 'in_review', 'completed', 'archived']
        if new_status in valid_statuses:
            self.status = new_status
            if reviewer_name:
                self.reviewer_name = reviewer_name
                if new_status == 'in_review':
                    self.review_started_at = datetime.utcnow()
                elif new_status == 'completed':
                    self.reviewed_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def get_status_display(self):
        """Get display text for status"""
        status_map = {
            'pending': 'Ожидает проверки',
            'in_review': f'На проверке: {self.reviewer_name}' if self.reviewer_name else 'На проверке',
            'completed': f'Проверено: {self.reviewer_name}' if self.reviewer_name else 'Проверено',
            'archived': 'Архив'
        }
        return status_map.get(self.status, self.status)
    
    @classmethod
    def get_reports_by_author(cls, discord_user_id):
        """Get all reports by a specific Discord user"""
        return cls.query.filter_by(discord_user_id=discord_user_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def create_from_discord_message(cls, user_id, username, server_id, channel_id, message_id, content):
        """Create a task report from a Discord message"""
        # Extract title from first line or use default
        lines = content.split('\n')
        title = lines[0] if lines else f"Отчет от {username}"
        description = '\n'.join(lines[1:]) if len(lines) > 1 else content
        
        report = cls(
            discord_user_id=str(user_id),
            discord_username=username,
            discord_server_id=str(server_id),
            discord_channel_id=str(channel_id),
            discord_message_id=str(message_id),
            title=title[:500],  # Ensure title fits in column
            description=description,
            status='pending'
        )
        return report
    
    @classmethod
    def get_reports_by_status(cls, status):
        """Get all reports by status"""
        return cls.query.filter_by(status=status).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_monthly_stats(cls):
        """Get monthly task report statistics"""
        from sqlalchemy import func, extract
        from datetime import datetime
        
        current_month = datetime.utcnow().replace(day=1)
        
        monthly_stats = db.session.query(
            func.count(cls.id).label('total_reports'),
            func.sum(cls.task_count).label('total_tasks'),
            func.sum(cls.approved_tasks).label('total_approved'),
            func.sum(cls.rejected_tasks).label('total_rejected')
        ).filter(
            cls.created_at >= current_month
        ).first()
        
        return {
            'total_reports': monthly_stats.total_reports or 0,
            'total_tasks': monthly_stats.total_tasks or 0,
            'total_approved': monthly_stats.total_approved or 0,
            'total_rejected': monthly_stats.total_rejected or 0,
            'approval_rate': round((monthly_stats.total_approved / monthly_stats.total_tasks * 100), 2) if monthly_stats.total_tasks else 0
        }
    
    @classmethod
    def get_recent_reports(cls, limit=20):
        """Get recent task reports"""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()
