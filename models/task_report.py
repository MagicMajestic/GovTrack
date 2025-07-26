# GovTracker2 Python Migration by Replit Agent
from database import db
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

class TaskReport(db.Model):
    __tablename__ = 'task_reports'
    
    # MySQL compatible AUTO_INCREMENT primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Report details
    author_id = Column(String(255), nullable=False, index=True)  # Discord ID of report author
    author_name = Column(String(255), nullable=False)
    
    # Task statistics
    task_count = Column(Integer, default=0)
    approved_tasks = Column(Integer, default=0)
    rejected_tasks = Column(Integer, default=0)
    
    # Report content
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Status using VARCHAR for MySQL compatibility
    status = Column(String(50), default='pending')  # pending, approved, rejected, archived
    
    # Timestamps using DATETIME for MySQL compatibility
    report_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TaskReport {self.title} by {self.author_name}>'
    
    def to_dict(self):
        """Convert task report to dictionary for JSON responses"""
        return {
            'id': self.id,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'task_count': self.task_count,
            'approved_tasks': self.approved_tasks,
            'rejected_tasks': self.rejected_tasks,
            'title': self.title,
            'description': self.description,
            'notes': self.notes,
            'status': self.status,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'approval_rate': self.get_approval_rate()
        }
    
    def get_approval_rate(self):
        """Calculate task approval rate"""
        if self.task_count == 0:
            return 0
        return round((self.approved_tasks / self.task_count) * 100, 2)
    
    def update_status(self, new_status):
        """Update report status with validation"""
        valid_statuses = ['pending', 'approved', 'rejected', 'archived']
        if new_status in valid_statuses:
            self.status = new_status
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    @classmethod
    def get_reports_by_author(cls, author_id):
        """Get all reports by a specific author"""
        return cls.query.filter_by(author_id=author_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_reports_by_status(cls, status):
        """Get reports filtered by status"""
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
