# GovTracker2 Python Migration by Replit Agent
from flask import Blueprint, request, jsonify
from app import db
from models.task_report import TaskReport
import logging
from datetime import datetime

task_reports_bp = Blueprint('task_reports', __name__)

@task_reports_bp.route('', methods=['GET'])
def get_task_reports():
    """Get list of task reports with optional filtering"""
    try:
        status = request.args.get('status')
        author_id = request.args.get('author_id')
        limit = request.args.get('limit', 50, type=int)
        
        query = TaskReport.query
        
        # Apply filters
        if status:
            query = query.filter_by(status=status)
        
        if author_id:
            query = query.filter_by(author_id=author_id)
        
        reports = query.order_by(TaskReport.created_at.desc()).limit(limit).all()
        reports_data = [report.to_dict() for report in reports]
        
        return jsonify(reports_data)
        
    except Exception as e:
        logging.error(f"Error getting task reports: {e}")
        return jsonify({'error': 'Failed to fetch task reports'}), 500

@task_reports_bp.route('/<int:report_id>', methods=['GET'])
def get_task_report(report_id):
    """Get specific task report details"""
    try:
        report = TaskReport.query.get_or_404(report_id)
        return jsonify(report.to_dict())
    except Exception as e:
        logging.error(f"Error getting task report {report_id}: {e}")
        return jsonify({'error': 'Task report not found'}), 404

@task_reports_bp.route('', methods=['POST'])
def create_task_report():
    """Create a new task report"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['author_id', 'author_name', 'title', 'task_count']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate task counts
        task_count = data['task_count']
        approved_tasks = data.get('approved_tasks', 0)
        rejected_tasks = data.get('rejected_tasks', 0)
        
        if approved_tasks + rejected_tasks > task_count:
            return jsonify({'error': 'Approved + rejected tasks cannot exceed total task count'}), 400
        
        # Create new task report
        report = TaskReport()
        report.author_id = str(data['author_id'])
        report.author_name = data['author_name']
        report.title = data['title']
        report.description = data.get('description')
        report.task_count = task_count
        report.approved_tasks = approved_tasks
        report.rejected_tasks = rejected_tasks
        report.notes = data.get('notes')
        report.status = data.get('status', 'pending')
        report.report_date = datetime.utcnow().date()
        report.created_at = datetime.utcnow()
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify(report.to_dict()), 201
        
    except Exception as e:
        logging.error(f"Error creating task report: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create task report'}), 500

@task_reports_bp.route('/<int:report_id>', methods=['PUT'])
def update_task_report(report_id):
    """Update task report information"""
    try:
        report = TaskReport.query.get_or_404(report_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'title' in data:
            report.title = data['title']
        if 'description' in data:
            report.description = data['description']
        if 'task_count' in data:
            report.task_count = data['task_count']
        if 'approved_tasks' in data:
            report.approved_tasks = data['approved_tasks']
        if 'rejected_tasks' in data:
            report.rejected_tasks = data['rejected_tasks']
        if 'notes' in data:
            report.notes = data['notes']
        if 'status' in data:
            if not report.update_status(data['status']):
                return jsonify({'error': 'Invalid status value'}), 400
        
        # Validate task counts after update
        if report.approved_tasks + report.rejected_tasks > report.task_count:
            return jsonify({'error': 'Approved + rejected tasks cannot exceed total task count'}), 400
        
        db.session.commit()
        
        return jsonify(report.to_dict())
        
    except Exception as e:
        logging.error(f"Error updating task report {report_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update task report'}), 500

@task_reports_bp.route('/<int:report_id>', methods=['DELETE'])
def delete_task_report(report_id):
    """Delete a task report"""
    try:
        report = TaskReport.query.get_or_404(report_id)
        
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({'message': 'Task report deleted successfully'})
        
    except Exception as e:
        logging.error(f"Error deleting task report {report_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete task report'}), 500

@task_reports_bp.route('/stats', methods=['GET'])
def get_task_report_stats():
    """Get task report statistics"""
    try:
        # Monthly statistics
        monthly_stats = TaskReport.get_monthly_stats()
        
        # Status breakdown
        from sqlalchemy import func
        
        status_breakdown = db.session.query(
            TaskReport.status,
            func.count(TaskReport.id).label('count')
        ).group_by(TaskReport.status).all()
        
        status_data = {}
        for item in status_breakdown:
            status_data[item.status] = item.count
        
        # Top contributors
        contributor_stats = db.session.query(
            TaskReport.author_id,
            TaskReport.author_name,
            func.count(TaskReport.id).label('report_count'),
            func.sum(TaskReport.task_count).label('total_tasks'),
            func.sum(TaskReport.approved_tasks).label('total_approved')
        ).group_by(
            TaskReport.author_id,
            TaskReport.author_name
        ).order_by(
            func.sum(TaskReport.task_count).desc()
        ).limit(10).all()
        
        top_contributors = []
        for stat in contributor_stats:
            approval_rate = 0
            if stat.total_tasks and stat.total_tasks > 0:
                approval_rate = round((stat.total_approved / stat.total_tasks) * 100, 2)
            
            top_contributors.append({
                'author_id': stat.author_id,
                'author_name': stat.author_name,
                'report_count': stat.report_count,
                'total_tasks': stat.total_tasks or 0,
                'total_approved': stat.total_approved or 0,
                'approval_rate': approval_rate
            })
        
        # Recent activity
        recent_reports = TaskReport.get_recent_reports(limit=10)
        recent_data = [report.to_dict() for report in recent_reports]
        
        stats_data = {
            'monthly_stats': monthly_stats,
            'status_breakdown': status_data,
            'top_contributors': top_contributors,
            'recent_reports': recent_data
        }
        
        return jsonify(stats_data)
        
    except Exception as e:
        logging.error(f"Error getting task report stats: {e}")
        return jsonify({'error': 'Failed to fetch task report statistics'}), 500

@task_reports_bp.route('/author/<author_id>', methods=['GET'])
def get_reports_by_author(author_id):
    """Get all reports by a specific author"""
    try:
        reports = TaskReport.get_reports_by_author(author_id)
        reports_data = [report.to_dict() for report in reports]
        
        # Calculate author statistics
        total_reports = len(reports)
        total_tasks = sum(report.task_count for report in reports)
        total_approved = sum(report.approved_tasks for report in reports)
        total_rejected = sum(report.rejected_tasks for report in reports)
        
        approval_rate = 0
        if total_tasks > 0:
            approval_rate = round((total_approved / total_tasks) * 100, 2)
        
        author_stats = {
            'author_id': author_id,
            'total_reports': total_reports,
            'total_tasks': total_tasks,
            'total_approved': total_approved,
            'total_rejected': total_rejected,
            'approval_rate': approval_rate
        }
        
        return jsonify({
            'author_stats': author_stats,
            'reports': reports_data
        })
        
    except Exception as e:
        logging.error(f"Error getting reports by author {author_id}: {e}")
        return jsonify({'error': 'Failed to fetch author reports'}), 500

@task_reports_bp.route('/<int:report_id>/status', methods=['PUT'])
def update_report_status(report_id):
    """Update report status only"""
    try:
        report = TaskReport.query.get_or_404(report_id)
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'error': 'Status field is required'}), 400
        
        if not report.update_status(data['status']):
            return jsonify({'error': 'Invalid status value'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': f'Report status updated to {report.status}',
            'report': report.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error updating report status for {report_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update report status'}), 500
