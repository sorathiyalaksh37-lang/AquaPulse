"""Monitoring routes for real-time water quality data"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.models import Reading, MonitoringNode, db
from backend.middleware.auth import get_current_user, role_required
from datetime import datetime, timedelta
from sqlalchemy import desc, and_
import json

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')

@monitoring_bp.route('/nodes', methods=['GET'])
def get_nodes():
    """Get all monitoring nodes"""
    try:
        # Check if user is authenticated for private nodes
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            user = get_current_user()
            if user and user.role in ['admin', 'government']:
                # Show all nodes
                nodes = MonitoringNode.query.all()
            else:
                # Show only public nodes
                nodes = MonitoringNode.query.filter_by(is_public=True).all()
        except:
            # Not authenticated, show only public nodes
            nodes = MonitoringNode.query.filter_by(is_public=True).all()
        
        return jsonify({
            'nodes': [node.to_dict() for node in nodes],
            'total': len(nodes)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get nodes', 'message': str(e)}), 500

@monitoring_bp.route('/nodes/<int:node_id>', methods=['GET'])
def get_node(node_id):
    """Get specific node details"""
    try:
        node = MonitoringNode.query.get(node_id)
        
        if not node:
            return jsonify({'error': 'Node not found'}), 404
        
        # Check if node is public or user has permission
        if not node.is_public:
            try:
                from flask_jwt_extended import verify_jwt_in_request
                verify_jwt_in_request()
                user = get_current_user()
                if not user or user.role not in ['admin', 'government']:
                    return jsonify({'error': 'Access denied'}), 403
            except:
                return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'node': node.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get node', 'message': str(e)}), 500

@monitoring_bp.route('/nodes', methods=['POST'])
@jwt_required()
@role_required('admin', 'government')
def create_node():
    """Create new monitoring node"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'location', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if hardware_id is unique
        if 'hardware_id' in data:
            existing = MonitoringNode.query.filter_by(hardware_id=data['hardware_id']).first()
            if existing:
                return jsonify({'error': 'Hardware ID already exists'}), 409
        
        node = MonitoringNode(
            name=data['name'],
            location=data['location'],
            ward=data.get('ward'),
            latitude=data['latitude'],
            longitude=data['longitude'],
            node_type=data.get('node_type', 'water_quality'),
            status=data.get('status', 'active'),
            hardware_id=data.get('hardware_id'),
            firmware_version=data.get('firmware_version'),
            description=data.get('description'),
            is_public=data.get('is_public', True),
            installed_at=datetime.utcnow()
        )
        
        if 'equipment_health' in data:
            node.set_equipment_health(data['equipment_health'])
        
        db.session.add(node)
        db.session.commit()
        
        return jsonify({
            'message': 'Node created successfully',
            'node': node.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create node', 'message': str(e)}), 500

@monitoring_bp.route('/nodes/<int:node_id>', methods=['PUT'])
@jwt_required()
@role_required('admin', 'government')
def update_node(node_id):
    """Update monitoring node"""
    try:
        node = MonitoringNode.query.get(node_id)
        
        if not node:
            return jsonify({'error': 'Node not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = ['name', 'location', 'ward', 'latitude', 'longitude', 'node_type', 
                         'status', 'firmware_version', 'description', 'is_public',
                         'last_calibration', 'next_maintenance']
        
        for field in allowed_fields:
            if field in data:
                if field in ['last_calibration', 'next_maintenance'] and data[field]:
                    setattr(node, field, datetime.fromisoformat(data[field]))
                else:
                    setattr(node, field, data[field])
        
        if 'equipment_health' in data:
            node.set_equipment_health(data['equipment_health'])
        
        node.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Node updated successfully',
            'node': node.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update node', 'message': str(e)}), 500

@monitoring_bp.route('/nodes/<int:node_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_node(node_id):
    """Delete monitoring node"""
    try:
        node = MonitoringNode.query.get(node_id)
        
        if not node:
            return jsonify({'error': 'Node not found'}), 404
        
        db.session.delete(node)
        db.session.commit()
        
        return jsonify({'message': 'Node deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete node', 'message': str(e)}), 500

@monitoring_bp.route('/readings', methods=['GET'])
def get_readings():
    """Get readings with filters"""
    try:
        # Query parameters
        node_id = request.args.get('node_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 100, type=int)
        status = request.args.get('status')  # Safe, Caution, Unsafe
        anomalies_only = request.args.get('anomalies_only', 'false').lower() == 'true'
        
        # Build query
        query = Reading.query
        
        if node_id:
            query = query.filter_by(node_id=node_id)
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            query = query.filter(Reading.timestamp >= start)
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            query = query.filter(Reading.timestamp <= end)
        
        if status:
            query = query.filter_by(overall_status=status)
        
        if anomalies_only:
            query = query.filter_by(is_anomaly=True)
        
        # Order by latest first and limit
        readings = query.order_by(desc(Reading.timestamp)).limit(limit).all()
        
        return jsonify({
            'readings': [reading.to_dict() for reading in readings],
            'total': len(readings)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get readings', 'message': str(e)}), 500

@monitoring_bp.route('/readings/latest', methods=['GET'])
def get_latest_reading():
    """Get latest reading for a node"""
    try:
        node_id = request.args.get('node_id', type=int)
        
        if node_id:
            reading = Reading.query.filter_by(node_id=node_id).order_by(desc(Reading.timestamp)).first()
        else:
            reading = Reading.query.order_by(desc(Reading.timestamp)).first()
        
        if not reading:
            return jsonify({'error': 'No readings available'}), 404
        
        return jsonify({'reading': reading.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get latest reading', 'message': str(e)}), 500

@monitoring_bp.route('/readings/stats', methods=['GET'])
def get_reading_stats():
    """Get statistics for readings"""
    try:
        node_id = request.args.get('node_id', type=int)
        hours = request.args.get('hours', 24, type=int)
        
        # Get readings from last N hours
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = Reading.query.filter(Reading.timestamp >= start_time)
        if node_id:
            query = query.filter_by(node_id=node_id)
        
        readings = query.all()
        
        if not readings:
            return jsonify({'error': 'No data available for the specified period'}), 404
        
        # Calculate statistics
        import numpy as np
        
        parameters = ['ph', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen']
        stats = {}
        
        for param in parameters:
            values = [getattr(r, param) for r in readings]
            stats[param] = {
                'current': values[-1],
                'min': round(min(values), 2),
                'max': round(max(values), 2),
                'avg': round(np.mean(values), 2),
                'median': round(np.median(values), 2),
                'std_dev': round(np.std(values), 2)
            }
        
        # Overall status distribution
        status_counts = {}
        for reading in readings:
            status = reading.overall_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return jsonify({
            'period': f'Last {hours} hours',
            'total_readings': len(readings),
            'statistics': stats,
            'status_distribution': status_counts,
            'anomaly_count': sum(1 for r in readings if r.is_anomaly)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get statistics', 'message': str(e)}), 500

@monitoring_bp.route('/readings/export', methods=['GET'])
@jwt_required()
def export_readings():
    """Export readings to CSV"""
    try:
        import csv
        from io import StringIO
        
        node_id = request.args.get('node_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = Reading.query
        
        if node_id:
            query = query.filter_by(node_id=node_id)
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            query = query.filter(Reading.timestamp >= start)
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            query = query.filter(Reading.timestamp <= end)
        
        readings = query.order_by(Reading.timestamp).all()
        
        if not readings:
            return jsonify({'error': 'No data to export'}), 404
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Timestamp', 'Node ID', 'pH', 'TDS', 'Turbidity', 'Temperature', 
                        'Conductivity', 'Dissolved Oxygen', 'Status', 'Anomaly'])
        
        # Data
        for reading in readings:
            writer.writerow([
                reading.timestamp.isoformat(),
                reading.node_id,
                reading.ph,
                reading.tds,
                reading.turbidity,
                reading.temperature,
                reading.conductivity,
                reading.dissolved_oxygen,
                reading.overall_status,
                reading.is_anomaly
            ])
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=readings_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': 'Failed to export data', 'message': str(e)}), 500
