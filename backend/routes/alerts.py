"""Alert management routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.models import Alert, Reading, MonitoringNode, db
from backend.middleware.auth import get_current_user, role_required
from datetime import datetime, timedelta
from sqlalchemy import desc, and_, or_

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@alerts_bp.route('/', methods=['GET'])
def get_alerts():
    """Get alerts with filters"""
    try:
        # Query parameters
        node_id = request.args.get('node_id', type=int)
        severity = request.args.get('severity')  # low, medium, high, critical
        alert_type = request.args.get('alert_type')  # contamination, anomaly, equipment, threshold
        status = request.args.get('status', 'active')  # active, acknowledged, resolved, all
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 50, type=int)
        
        # Build query
        query = Alert.query
        
        if node_id:
            query = query.filter_by(node_id=node_id)
        
        if severity:
            query = query.filter_by(severity=severity)
        
        if alert_type:
            query = query.filter_by(alert_type=alert_type)
        
        if status != 'all':
            query = query.filter_by(status=status)
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            query = query.filter(Alert.timestamp >= start)
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            query = query.filter(Alert.timestamp <= end)
        
        # Order by latest first and limit
        alerts = query.order_by(desc(Alert.timestamp)).limit(limit).all()
        
        return jsonify({
            'alerts': [alert.to_dict() for alert in alerts],
            'total': len(alerts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get alerts', 'message': str(e)}), 500

@alerts_bp.route('/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get specific alert details"""
    try:
        alert = Alert.query.get(alert_id)
        
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        return jsonify({'alert': alert.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get alert', 'message': str(e)}), 500

@alerts_bp.route('/<int:alert_id>/acknowledge', methods=['POST'])
@jwt_required()
@role_required('admin', 'government')
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    try:
        alert = Alert.query.get(alert_id)
        
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        if alert.status != 'active':
            return jsonify({'error': 'Alert is not active'}), 400
        
        user = get_current_user()
        
        alert.status = 'acknowledged'
        alert.acknowledged_by = user.id
        alert.acknowledged_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Alert acknowledged successfully',
            'alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to acknowledge alert', 'message': str(e)}), 500

@alerts_bp.route('/<int:alert_id>/resolve', methods=['POST'])
@jwt_required()
@role_required('admin', 'government')
def resolve_alert(alert_id):
    """Resolve an alert"""
    try:
        alert = Alert.query.get(alert_id)
        
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        if alert.status == 'resolved':
            return jsonify({'error': 'Alert is already resolved'}), 400
        
        data = request.get_json()
        user = get_current_user()
        
        alert.status = 'resolved'
        alert.resolved_by = user.id
        alert.resolved_at = datetime.utcnow()
        alert.resolution_notes = data.get('resolution_notes', '')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Alert resolved successfully',
            'alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to resolve alert', 'message': str(e)}), 500

@alerts_bp.route('/stats', methods=['GET'])
def get_alert_stats():
    """Get alert statistics"""
    try:
        hours = request.args.get('hours', 24, type=int)
        node_id = request.args.get('node_id', type=int)
        
        # Get alerts from last N hours
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = Alert.query.filter(Alert.timestamp >= start_time)
        if node_id:
            query = query.filter_by(node_id=node_id)
        
        alerts = query.all()
        
        # Calculate statistics
        stats = {
            'total': len(alerts),
            'active': sum(1 for a in alerts if a.status == 'active'),
            'acknowledged': sum(1 for a in alerts if a.status == 'acknowledged'),
            'resolved': sum(1 for a in alerts if a.status == 'resolved'),
            'by_severity': {
                'low': sum(1 for a in alerts if a.severity == 'low'),
                'medium': sum(1 for a in alerts if a.severity == 'medium'),
                'high': sum(1 for a in alerts if a.severity == 'high'),
                'critical': sum(1 for a in alerts if a.severity == 'critical')
            },
            'by_type': {
                'contamination': sum(1 for a in alerts if a.alert_type == 'contamination'),
                'anomaly': sum(1 for a in alerts if a.alert_type == 'anomaly'),
                'equipment': sum(1 for a in alerts if a.alert_type == 'equipment'),
                'threshold': sum(1 for a in alerts if a.alert_type == 'threshold')
            },
            'period': f'Last {hours} hours'
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get alert statistics', 'message': str(e)}), 500

@alerts_bp.route('/recent', methods=['GET'])
def get_recent_alerts():
    """Get recent critical and high severity alerts"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        alerts = Alert.query.filter(
            or_(Alert.severity == 'critical', Alert.severity == 'high')
        ).filter_by(status='active').order_by(desc(Alert.timestamp)).limit(limit).all()
        
        return jsonify({
            'alerts': [alert.to_dict() for alert in alerts],
            'count': len(alerts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get recent alerts', 'message': str(e)}), 500

@alerts_bp.route('/bulk-resolve', methods=['POST'])
@jwt_required()
@role_required('admin', 'government')
def bulk_resolve_alerts():
    """Resolve multiple alerts at once"""
    try:
        data = request.get_json()
        alert_ids = data.get('alert_ids', [])
        resolution_notes = data.get('resolution_notes', '')
        
        if not alert_ids:
            return jsonify({'error': 'No alert IDs provided'}), 400
        
        user = get_current_user()
        resolved_count = 0
        
        for alert_id in alert_ids:
            alert = Alert.query.get(alert_id)
            if alert and alert.status != 'resolved':
                alert.status = 'resolved'
                alert.resolved_by = user.id
                alert.resolved_at = datetime.utcnow()
                alert.resolution_notes = resolution_notes
                resolved_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'{resolved_count} alerts resolved successfully',
            'resolved_count': resolved_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to resolve alerts', 'message': str(e)}), 500
