"""Reports routes for generating and managing compliance reports"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from backend.models import Report, Reading, MonitoringNode, db
from backend.services.report_service import report_service
from backend.middleware.auth import get_current_user, role_required
from datetime import datetime, timedelta
from sqlalchemy import desc
import json

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@reports_bp.route('/generate/cpcb', methods=['POST'])
@jwt_required()
@role_required('admin', 'government')
def generate_cpcb_report():
    """Generate CPCB BIS 10500:2012 compliance report"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        # Get date range
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        node_id = data.get('node_id')
        
        if not start_date_str or not end_date_str:
            # Default to last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        
        # Get readings
        query = Reading.query.filter(
            Reading.timestamp >= start_date,
            Reading.timestamp <= end_date
        )
        
        if node_id:
            query = query.filter_by(node_id=node_id)
        
        readings = query.all()
        
        if not readings:
            return jsonify({'error': 'No data available for the specified period'}), 404
        
        # Convert to format for report service
        readings_data = []
        for reading in readings:
            readings_data.append({
                'timestamp': reading.timestamp.isoformat(),
                'pH': reading.ph,
                'tds': reading.tds,
                'turbidity': reading.turbidity,
                'temperature': reading.temperature,
                'conductivity': reading.conductivity,
                'dissolved_oxygen': reading.dissolved_oxygen,
                'overall_status': reading.overall_status
            })
        
        # Get node info if specified
        node_info = None
        if node_id:
            node = MonitoringNode.query.get(node_id)
            if node:
                node_info = node.to_dict()
        
        # Generate report
        report_data, error = report_service.generate_cpcb_report(
            readings_data,
            start_date,
            end_date,
            node_info
        )
        
        if error:
            return jsonify({'error': error}), 500
        
        # Save report to database
        report = Report(
            report_id=report_data['report_id'],
            report_type='cpcb',
            title=report_data['title'],
            start_date=start_date,
            end_date=end_date,
            generated_by=user.id,
            report_data=json.dumps(report_data),
            summary=report_data.get('summary', ''),
            compliance_score=report_data.get('compliance_score', 0)
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'message': 'CPCB report generated successfully',
            'report': report_data
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Report generation failed', 'message': str(e)}), 500

@reports_bp.route('/generate/daily', methods=['POST'])
@jwt_required()
@role_required('admin', 'government')
def generate_daily_report():
    """Generate daily summary report"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        # Get date
        date_str = data.get('date')
        if not date_str:
            date = datetime.utcnow().date()
        else:
            date = datetime.fromisoformat(date_str).date()
        
        # Get readings for the day
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())
        
        readings = Reading.query.filter(
            Reading.timestamp >= start_time,
            Reading.timestamp <= end_time
        ).all()
        
        if not readings:
            return jsonify({'error': 'No data available for the specified date'}), 404
        
        # Convert to format for report service
        readings_data = []
        for reading in readings:
            readings_data.append({
                'timestamp': reading.timestamp.isoformat(),
                'pH': reading.ph,
                'tds': reading.tds,
                'turbidity': reading.turbidity,
                'temperature': reading.temperature,
                'conductivity': reading.conductivity,
                'dissolved_oxygen': reading.dissolved_oxygen,
                'overall_status': reading.overall_status,
                'is_anomaly': reading.is_anomaly
            })
        
        # Generate report
        report_data, error = report_service.generate_daily_report(readings_data, datetime.combine(date, datetime.min.time()))
        
        if error:
            return jsonify({'error': error}), 500
        
        # Save to database
        report = Report(
            report_id=report_data['report_id'],
            report_type='daily',
            title=report_data['title'],
            start_date=start_time,
            end_date=end_time,
            generated_by=user.id,
            report_data=json.dumps(report_data),
            summary=report_data.get('summary', ''),
            is_automated=data.get('automated', False)
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'message': 'Daily report generated successfully',
            'report': report_data
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Daily report generation failed', 'message': str(e)}), 500

@reports_bp.route('/generate/weekly', methods=['POST'])
@jwt_required()
@role_required('admin', 'government')
def generate_weekly_report():
    """Generate weekly compliance report"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        # Get date range (default to last 7 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        if 'start_date' in data:
            start_date = datetime.fromisoformat(data['start_date'])
        if 'end_date' in data:
            end_date = datetime.fromisoformat(data['end_date'])
        
        # Get readings
        readings = Reading.query.filter(
            Reading.timestamp >= start_date,
            Reading.timestamp <= end_date
        ).all()
        
        if not readings:
            return jsonify({'error': 'No data available for the specified period'}), 404
        
        # Convert to format for report service
        readings_data = []
        for reading in readings:
            readings_data.append({
                'timestamp': reading.timestamp.isoformat(),
                'pH': reading.ph,
                'tds': reading.tds,
                'turbidity': reading.turbidity,
                'temperature': reading.temperature,
                'conductivity': reading.conductivity,
                'dissolved_oxygen': reading.dissolved_oxygen,
                'overall_status': reading.overall_status,
                'is_anomaly': reading.is_anomaly
            })
        
        # Generate report
        report_data, error = report_service.generate_weekly_report(readings_data, start_date, end_date)
        
        if error:
            return jsonify({'error': error}), 500
        
        # Save to database
        report = Report(
            report_id=report_data['report_id'],
            report_type='weekly',
            title=report_data['title'],
            start_date=start_date,
            end_date=end_date,
            generated_by=user.id,
            report_data=json.dumps(report_data),
            summary=report_data.get('summary', ''),
            is_automated=data.get('automated', False)
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'message': 'Weekly report generated successfully',
            'report': report_data
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Weekly report generation failed', 'message': str(e)}), 500

@reports_bp.route('/', methods=['GET'])
@jwt_required()
def get_reports():
    """Get all reports with filters"""
    try:
        report_type = request.args.get('type')  # cpcb, daily, weekly, monthly
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 50, type=int)
        
        query = Report.query
        
        if report_type:
            query = query.filter_by(report_type=report_type)
        
        if start_date:
            start = datetime.fromisoformat(start_date)
            query = query.filter(Report.generated_at >= start)
        
        if end_date:
            end = datetime.fromisoformat(end_date)
            query = query.filter(Report.generated_at <= end)
        
        reports = query.order_by(desc(Report.generated_at)).limit(limit).all()
        
        return jsonify({
            'reports': [report.to_dict() for report in reports],
            'total': len(reports)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get reports', 'message': str(e)}), 500

@reports_bp.route('/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    """Get specific report details"""
    try:
        report = Report.query.get(report_id)
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Parse report data
        report_dict = report.to_dict()
        if report.report_data:
            report_dict['data'] = json.loads(report.report_data)
        
        return jsonify({'report': report_dict}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get report', 'message': str(e)}), 500

@reports_bp.route('/<report_id>/export', methods=['GET'])
@jwt_required()
def export_report(report_id):
    """Export report to CSV/PDF/Excel"""
    try:
        report = Report.query.filter_by(report_id=report_id).first()
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        format_type = request.args.get('format', 'csv')  # csv, pdf, excel
        
        # Parse report data
        report_data = json.loads(report.report_data) if report.report_data else {}
        
        if format_type == 'csv':
            filepath, error = report_service.export_to_csv(report_data)
            if error:
                return jsonify({'error': error}), 500
            return send_file(filepath, as_attachment=True, download_name=f"{report_id}.csv")
        
        elif format_type == 'pdf':
            filepath, error = report_service.export_to_pdf(report_data)
            if error:
                return jsonify({'error': error}), 500
            # For now, return text file
            return send_file(filepath.replace('.pdf', '.txt'), as_attachment=True, download_name=f"{report_id}.txt")
        
        else:
            return jsonify({'error': 'Invalid format. Supported: csv, pdf'}), 400
        
    except Exception as e:
        return jsonify({'error': 'Export failed', 'message': str(e)}), 500

@reports_bp.route('/<int:report_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_report(report_id):
    """Delete a report"""
    try:
        report = Report.query.get(report_id)
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({'message': 'Report deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete report', 'message': str(e)}), 500

@reports_bp.route('/schedule', methods=['POST'])
@jwt_required()
@role_required('admin')
def schedule_report():
    """Schedule automated report generation (placeholder)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['report_type', 'frequency', 'recipients']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # TODO: Implement with APScheduler or Celery
        # For now, return success
        
        return jsonify({
            'message': 'Report scheduled successfully',
            'schedule': {
                'report_type': data['report_type'],
                'frequency': data['frequency'],
                'recipients': data['recipients'],
                'next_run': (datetime.utcnow() + timedelta(days=1)).isoformat()
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': 'Scheduling failed', 'message': str(e)}), 500

@reports_bp.route('/schedules', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_schedules():
    """Get all scheduled reports (placeholder)"""
    try:
        # TODO: Implement with APScheduler or Celery
        # For now, return empty list
        
        return jsonify({
            'schedules': [],
            'message': 'No scheduled reports configured'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get schedules', 'message': str(e)}), 500
