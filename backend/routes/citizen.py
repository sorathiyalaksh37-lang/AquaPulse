"""Citizen portal routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.models import CitizenReport, Reading, MonitoringNode, User, db
from backend.middleware.auth import get_current_user, role_required
from datetime import datetime, timedelta
from sqlalchemy import desc
from werkzeug.utils import secure_filename
import os

citizen_bp = Blueprint('citizen', __name__, url_prefix='/api/citizen')

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads/citizen_reports'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@citizen_bp.route('/dashboard', methods=['GET'])
def get_public_dashboard():
    """Get public water quality dashboard data"""
    try:
        ward = request.args.get('ward')
        
        # Get all public nodes
        query = MonitoringNode.query.filter_by(is_public=True, status='active')
        if ward:
            query = query.filter_by(ward=ward)
        
        nodes = query.all()
        
        # Get latest readings for each node
        dashboard_data = []
        for node in nodes:
            latest_reading = Reading.query.filter_by(node_id=node.id).order_by(desc(Reading.timestamp)).first()
            if latest_reading:
                dashboard_data.append({
                    'node': node.to_dict(),
                    'latest_reading': latest_reading.to_dict()
                })
        
        # Calculate overall safety status
        safe_count = sum(1 for d in dashboard_data if d['latest_reading']['overall_status'] == 'Safe')
        total_count = len(dashboard_data)
        
        overall_status = 'Safe' if total_count > 0 and safe_count == total_count else \
                        'Unsafe' if safe_count == 0 else 'Caution'
        
        return jsonify({
            'overall_status': overall_status,
            'safe_nodes': safe_count,
            'total_nodes': total_count,
            'nodes_data': dashboard_data,
            'last_updated': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get public dashboard', 'message': str(e)}), 500

@citizen_bp.route('/report-issue', methods=['POST'])
@jwt_required()
def report_issue():
    """Submit a water quality issue report"""
    try:
        user = get_current_user()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Handle multipart form data
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        severity = request.form.get('severity', 'medium')
        location = request.form.get('location')
        ward = request.form.get('ward')
        latitude = request.form.get('latitude', type=float)
        longitude = request.form.get('longitude', type=float)
        
        # Validate required fields
        if not all([title, description, category]):
            return jsonify({'error': 'Title, description, and category are required'}), 400
        
        # Validate category
        valid_categories = ['taste', 'odor', 'color', 'pressure', 'other']
        if category not in valid_categories:
            return jsonify({'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'}), 400
        
        # Handle photo upload
        photo_path = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename and allowed_file(photo.filename):
                # Create upload directory if it doesn't exist
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                # Generate unique filename
                filename = secure_filename(f"{user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{photo.filename}")
                photo_path = os.path.join(UPLOAD_FOLDER, filename)
                photo.save(photo_path)
        
        # Create report
        report = CitizenReport(
            user_id=user.id,
            title=title,
            description=description,
            category=category,
            severity=severity,
            location=location,
            ward=ward,
            latitude=latitude,
            longitude=longitude,
            photo_path=photo_path,
            submitted_at=datetime.utcnow()
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'message': 'Issue reported successfully. Our team will investigate.',
            'report': report.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to submit report', 'message': str(e)}), 500

@citizen_bp.route('/my-reports', methods=['GET'])
@jwt_required()
def get_my_reports():
    """Get current user's submitted reports"""
    try:
        user = get_current_user()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        status = request.args.get('status')  # submitted, investigating, resolved, closed
        limit = request.args.get('limit', 20, type=int)
        
        query = CitizenReport.query.filter_by(user_id=user.id)
        
        if status:
            query = query.filter_by(status=status)
        
        reports = query.order_by(desc(CitizenReport.submitted_at)).limit(limit).all()
        
        return jsonify({
            'reports': [report.to_dict() for report in reports],
            'total': len(reports)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get reports', 'message': str(e)}), 500

@citizen_bp.route('/reports/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    """Get specific report details"""
    try:
        report = CitizenReport.query.get(report_id)
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        user = get_current_user()
        
        # Check if user owns the report or is admin/government
        if report.user_id != user.id and user.role not in ['admin', 'government']:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'report': report.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get report', 'message': str(e)}), 500

@citizen_bp.route('/reports', methods=['GET'])
@jwt_required()
@role_required('admin', 'government')
def get_all_reports():
    """Get all citizen reports (admin/government only)"""
    try:
        status = request.args.get('status')
        category = request.args.get('category')
        severity = request.args.get('severity')
        ward = request.args.get('ward')
        limit = request.args.get('limit', 50, type=int)
        
        query = CitizenReport.query
        
        if status:
            query = query.filter_by(status=status)
        
        if category:
            query = query.filter_by(category=category)
        
        if severity:
            query = query.filter_by(severity=severity)
        
        if ward:
            query = query.filter_by(ward=ward)
        
        reports = query.order_by(desc(CitizenReport.submitted_at)).limit(limit).all()
        
        # Get user info for each report
        reports_with_users = []
        for report in reports:
            report_dict = report.to_dict()
            user = User.query.get(report.user_id)
            if user:
                report_dict['user'] = {
                    'full_name': user.full_name,
                    'email': user.email,
                    'phone': user.phone
                }
            reports_with_users.append(report_dict)
        
        return jsonify({
            'reports': reports_with_users,
            'total': len(reports)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get reports', 'message': str(e)}), 500

@citizen_bp.route('/reports/<int:report_id>/update-status', methods=['PUT'])
@jwt_required()
@role_required('admin', 'government')
def update_report_status(report_id):
    """Update citizen report status"""
    try:
        report = CitizenReport.query.get(report_id)
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        data = request.get_json()
        user = get_current_user()
        
        # Update status
        if 'status' in data:
            valid_statuses = ['submitted', 'investigating', 'resolved', 'closed']
            if data['status'] not in valid_statuses:
                return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
            report.status = data['status']
        
        # Update priority
        if 'priority' in data:
            valid_priorities = ['low', 'normal', 'high', 'urgent']
            if data['priority'] not in valid_priorities:
                return jsonify({'error': f'Invalid priority. Must be one of: {", ".join(valid_priorities)}'}), 400
            report.priority = data['priority']
        
        # Assign to user
        if 'assigned_to' in data:
            report.assigned_to = data['assigned_to']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Report status updated successfully',
            'report': report.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update report status', 'message': str(e)}), 500

@citizen_bp.route('/reports/<int:report_id>/respond', methods=['POST'])
@jwt_required()
@role_required('admin', 'government')
def respond_to_report(report_id):
    """Add response to citizen report"""
    try:
        report = CitizenReport.query.get(report_id)
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        data = request.get_json()
        user = get_current_user()
        
        if 'response' not in data:
            return jsonify({'error': 'Response text is required'}), 400
        
        report.response = data['response']
        report.response_by = user.id
        report.response_at = datetime.utcnow()
        
        # Auto-resolve if requested
        if data.get('resolve', False):
            report.status = 'resolved'
            report.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        # TODO: Send notification to the citizen
        
        return jsonify({
            'message': 'Response added successfully',
            'report': report.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add response', 'message': str(e)}), 500

@citizen_bp.route('/stats', methods=['GET'])
@jwt_required()
@role_required('admin', 'government')
def get_citizen_stats():
    """Get citizen report statistics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get reports from last N days
        start_time = datetime.utcnow() - timedelta(days=days)
        reports = CitizenReport.query.filter(CitizenReport.submitted_at >= start_time).all()
        
        stats = {
            'total': len(reports),
            'by_status': {
                'submitted': sum(1 for r in reports if r.status == 'submitted'),
                'investigating': sum(1 for r in reports if r.status == 'investigating'),
                'resolved': sum(1 for r in reports if r.status == 'resolved'),
                'closed': sum(1 for r in reports if r.status == 'closed')
            },
            'by_category': {
                'taste': sum(1 for r in reports if r.category == 'taste'),
                'odor': sum(1 for r in reports if r.category == 'odor'),
                'color': sum(1 for r in reports if r.category == 'color'),
                'pressure': sum(1 for r in reports if r.category == 'pressure'),
                'other': sum(1 for r in reports if r.category == 'other')
            },
            'by_severity': {
                'low': sum(1 for r in reports if r.severity == 'low'),
                'medium': sum(1 for r in reports if r.severity == 'medium'),
                'high': sum(1 for r in reports if r.severity == 'high')
            },
            'period': f'Last {days} days'
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get statistics', 'message': str(e)}), 500

@citizen_bp.route('/education', methods=['GET'])
def get_educational_content():
    """Get educational resources about water quality"""
    return jsonify({
        'resources': [
            {
                'title': 'Understanding Water Quality Parameters',
                'description': 'Learn about pH, TDS, turbidity, and other important water quality indicators.',
                'content': {
                    'pH': 'pH measures the acidity or alkalinity of water. Safe drinking water should have a pH between 6.5 and 8.5.',
                    'TDS': 'Total Dissolved Solids (TDS) indicates the total amount of dissolved minerals. Safe limit is below 500 ppm.',
                    'Turbidity': 'Turbidity measures water cloudiness. Clear water should have turbidity below 5 NTU.',
                    'Temperature': 'Water temperature affects taste and microbial growth. Ideal range is 15-35°C.',
                    'Conductivity': 'Conductivity indicates dissolved ionic substances. Safe range is 0-1000 µS/cm.',
                    'Dissolved Oxygen': 'DO indicates oxygen dissolved in water. Healthy water has DO between 5-14 mg/L.'
                }
            },
            {
                'title': 'Water Safety Guidelines',
                'description': 'Essential safety tips for drinking water.',
                'tips': [
                    'Always boil water if you notice unusual taste, odor, or color',
                    'Store drinking water in clean, covered containers',
                    'Check for government advisories regularly',
                    'Report any water quality concerns immediately',
                    'Use water filters certified by recognized authorities',
                    'Maintain clean water storage tanks and pipelines'
                ]
            },
            {
                'title': 'Common Water Quality Issues',
                'description': 'Identify and report common water problems.',
                'issues': [
                    {'problem': 'Cloudy/Turbid Water', 'cause': 'Suspended particles, sediment', 'action': 'Report immediately, avoid consumption'},
                    {'problem': 'Bad Smell', 'cause': 'Organic matter, chlorine, or contamination', 'action': 'Report and get tested'},
                    {'problem': 'Unusual Color', 'cause': 'Rust, algae, or chemical contamination', 'action': 'Do not consume, report urgently'},
                    {'problem': 'Bitter/Metallic Taste', 'cause': 'High TDS, minerals, or pipe corrosion', 'action': 'Get water tested'},
                    {'problem': 'Low Pressure', 'cause': 'Pipeline issues or supply problems', 'action': 'Report to authorities'}
                ]
            },
            {
                'title': 'BIS 10500:2012 Standards',
                'description': 'Indian standards for drinking water quality.',
                'standards': {
                    'pH': '6.5 - 8.5',
                    'TDS': '< 500 ppm (desirable), < 2000 ppm (permissible)',
                    'Turbidity': '< 5 NTU (desirable), < 10 NTU (permissible)',
                    'Temperature': '15 - 35°C',
                    'Conductivity': '< 1000 µS/cm',
                    'Dissolved Oxygen': '5 - 14 mg/L'
                }
            }
        ]
    }), 200
