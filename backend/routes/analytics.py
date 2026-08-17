"""Analytics routes for AI-powered predictions and insights"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.models import Reading, MonitoringNode, db
from backend.services.ai_service import ai_service
from backend.middleware.auth import role_required
from datetime import datetime, timedelta
from sqlalchemy import desc
import pandas as pd

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/forecast', methods=['GET'])
@jwt_required()
def get_forecast():
    """Get 24-hour forecast for water quality parameters"""
    try:
        node_id = request.args.get('node_id', type=int)
        parameter = request.args.get('parameter')  # Optional: specific parameter
        
        # Get historical data (last 7 days for better prediction)
        start_time = datetime.utcnow() - timedelta(days=7)
        
        query = Reading.query.filter(Reading.timestamp >= start_time)
        if node_id:
            query = query.filter_by(node_id=node_id)
        
        readings = query.order_by(Reading.timestamp).all()
        
        if len(readings) < 24:
            return jsonify({'error': 'Insufficient historical data for forecasting (need at least 24 readings)'}), 400
        
        # Convert to format needed for AI service
        historical_data = []
        for reading in readings:
            historical_data.append({
                'timestamp': reading.timestamp.isoformat(),
                'pH': reading.ph,
                'tds': reading.tds,
                'turbidity': reading.turbidity,
                'temperature': reading.temperature,
                'conductivity': reading.conductivity,
                'dissolved_oxygen': reading.dissolved_oxygen
            })
        
        # Get forecast
        forecast_data, error = ai_service.forecast_24h(historical_data, parameter)
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'forecast': forecast_data,
            'historical_data_points': len(historical_data),
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Forecast generation failed', 'message': str(e)}), 500

@analytics_bp.route('/anomaly-detection', methods=['POST'])
@jwt_required()
def detect_anomaly():
    """Detect anomaly in a water quality reading"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required = ['pH', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen']
        for param in required:
            if param not in data:
                return jsonify({'error': f'Missing parameter: {param}'}), 400
        
        # Detect anomaly
        is_anomaly, anomaly_score, message = ai_service.detect_anomaly(data)
        
        if message != "Success":
            return jsonify({'error': message}), 500
        
        # Determine severity
        if anomaly_score > 0.8:
            severity = 'critical'
        elif anomaly_score > 0.5:
            severity = 'high'
        elif anomaly_score > 0.3:
            severity = 'medium'
        else:
            severity = 'low'
        
        return jsonify({
            'is_anomaly': is_anomaly,
            'anomaly_score': round(anomaly_score, 3),
            'severity': severity if is_anomaly else 'normal',
            'parameters': data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Anomaly detection failed', 'message': str(e)}), 500

@analytics_bp.route('/train-model', methods=['POST'])
@jwt_required()
@role_required('admin')
def train_model():
    """Train AI models with historical data"""
    try:
        # Get all historical readings
        readings = Reading.query.order_by(Reading.timestamp).all()
        
        if len(readings) < 100:
            return jsonify({'error': 'Insufficient data for training (need at least 100 readings)'}), 400
        
        # Convert to DataFrame
        data = pd.DataFrame([{
            'pH': r.ph,
            'tds': r.tds,
            'turbidity': r.turbidity,
            'temperature': r.temperature,
            'conductivity': r.conductivity,
            'dissolved_oxygen': r.dissolved_oxygen
        } for r in readings])
        
        # Train Isolation Forest
        success, message = ai_service.train_isolation_forest(data)
        
        if not success:
            return jsonify({'error': message}), 500
        
        return jsonify({
            'message': 'Model training completed successfully',
            'training_samples': len(readings),
            'trained_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Model training failed', 'message': str(e)}), 500

@analytics_bp.route('/predictive-maintenance', methods=['GET'])
@jwt_required()
@role_required('admin', 'government')
def get_predictive_maintenance():
    """Get predictive maintenance insights for equipment"""
    try:
        node_id = request.args.get('node_id', type=int)
        
        if not node_id:
            return jsonify({'error': 'node_id is required'}), 400
        
        node = MonitoringNode.query.get(node_id)
        
        if not node:
            return jsonify({'error': 'Node not found'}), 404
        
        # Get equipment health data
        equipment_health = node.get_equipment_health()
        
        # Add usage data (simulated for now)
        for equipment in equipment_health:
            equipment_health[equipment]['last_maintenance_days'] = 30  # Example
            equipment_health[equipment]['usage_hours'] = 720  # Example: 30 days * 24 hours
        
        # Get predictions
        predictions, error = ai_service.predict_maintenance(equipment_health)
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'node_id': node_id,
            'node_name': node.name,
            'predictions': predictions,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Predictive maintenance failed', 'message': str(e)}), 500

@analytics_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    """Get trend analysis for water quality parameters"""
    try:
        node_id = request.args.get('node_id', type=int)
        period = request.args.get('period', 'monthly')  # daily, weekly, monthly
        months = request.args.get('months', 3, type=int)  # Last N months
        
        # Get historical data
        start_time = datetime.utcnow() - timedelta(days=months*30)
        
        query = Reading.query.filter(Reading.timestamp >= start_time)
        if node_id:
            query = query.filter_by(node_id=node_id)
        
        readings = query.order_by(Reading.timestamp).all()
        
        if len(readings) < 10:
            return jsonify({'error': 'Insufficient data for trend analysis'}), 400
        
        # Convert to format for AI service
        historical_data = []
        for reading in readings:
            historical_data.append({
                'timestamp': reading.timestamp.isoformat(),
                'pH': reading.ph,
                'tds': reading.tds,
                'turbidity': reading.turbidity,
                'temperature': reading.temperature,
                'conductivity': reading.conductivity,
                'dissolved_oxygen': reading.dissolved_oxygen
            })
        
        # Analyze trends
        trends, error = ai_service.analyze_trends(historical_data, period)
        
        if error:
            return jsonify({'error': error}), 500
        
        return jsonify({
            'trends': trends,
            'period': period,
            'data_points': len(readings),
            'start_date': start_time.isoformat(),
            'end_date': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Trend analysis failed', 'message': str(e)}), 500

@analytics_bp.route('/anomaly-history', methods=['GET'])
@jwt_required()
def get_anomaly_history():
    """Get history of detected anomalies"""
    try:
        node_id = request.args.get('node_id', type=int)
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Get anomalous readings
        start_time = datetime.utcnow() - timedelta(days=days)
        
        query = Reading.query.filter(
            Reading.timestamp >= start_time,
            Reading.is_anomaly == True
        )
        
        if node_id:
            query = query.filter_by(node_id=node_id)
        
        anomalies = query.order_by(desc(Reading.timestamp)).limit(limit).all()
        
        # Group by date for pattern analysis
        anomaly_dates = {}
        for anomaly in anomalies:
            date = anomaly.timestamp.date().isoformat()
            if date not in anomaly_dates:
                anomaly_dates[date] = 0
            anomaly_dates[date] += 1
        
        return jsonify({
            'anomalies': [a.to_dict() for a in anomalies],
            'total': len(anomalies),
            'by_date': anomaly_dates,
            'period': f'Last {days} days'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get anomaly history', 'message': str(e)}), 500

@analytics_bp.route('/correlation-analysis', methods=['GET'])
@jwt_required()
def get_correlation_analysis():
    """Get correlation analysis between parameters"""
    try:
        node_id = request.args.get('node_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        # Get readings
        start_time = datetime.utcnow() - timedelta(days=days)
        
        query = Reading.query.filter(Reading.timestamp >= start_time)
        if node_id:
            query = query.filter_by(node_id=node_id)
        
        readings = query.all()
        
        if len(readings) < 10:
            return jsonify({'error': 'Insufficient data for correlation analysis'}), 400
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'pH': r.ph,
            'tds': r.tds,
            'turbidity': r.turbidity,
            'temperature': r.temperature,
            'conductivity': r.conductivity,
            'dissolved_oxygen': r.dissolved_oxygen
        } for r in readings])
        
        # Calculate correlation matrix
        correlation_matrix = df.corr().round(3).to_dict()
        
        # Find strong correlations
        strong_correlations = []
        parameters = list(correlation_matrix.keys())
        for i, param1 in enumerate(parameters):
            for param2 in parameters[i+1:]:
                corr_value = correlation_matrix[param1][param2]
                if abs(corr_value) > 0.5:  # Strong correlation threshold
                    strong_correlations.append({
                        'parameter1': param1,
                        'parameter2': param2,
                        'correlation': corr_value,
                        'strength': 'strong positive' if corr_value > 0.7 else 'strong negative' if corr_value < -0.7 else 'moderate'
                    })
        
        return jsonify({
            'correlation_matrix': correlation_matrix,
            'strong_correlations': strong_correlations,
            'data_points': len(readings),
            'period': f'Last {days} days'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Correlation analysis failed', 'message': str(e)}), 500

@analytics_bp.route('/model-info', methods=['GET'])
@jwt_required()
def get_model_info():
    """Get information about loaded AI models"""
    try:
        info = ai_service.get_model_info()
        
        return jsonify({
            'models': info,
            'status': 'operational' if info['isolation_forest'] else 'training_required'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get model info', 'message': str(e)}), 500

@analytics_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_advanced_statistics():
    """Get advanced statistical analysis"""
    try:
        node_id = request.args.get('node_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        # Get readings
        start_time = datetime.utcnow() - timedelta(days=days)
        
        query = Reading.query.filter(Reading.timestamp >= start_time)
        if node_id:
            query = query.filter_by(node_id=node_id)
        
        readings = query.all()
        
        if not readings:
            return jsonify({'error': 'No data available'}), 404
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'pH': r.ph,
            'tds': r.tds,
            'turbidity': r.turbidity,
            'temperature': r.temperature,
            'conductivity': r.conductivity,
            'dissolved_oxygen': r.dissolved_oxygen,
            'overall_status': r.overall_status
        } for r in readings])
        
        # Calculate advanced statistics
        statistics = {}
        for param in ['pH', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen']:
            values = df[param].values
            statistics[param] = {
                'mean': round(float(values.mean()), 2),
                'median': round(float(np.median(values)), 2),
                'std': round(float(values.std()), 2),
                'min': round(float(values.min()), 2),
                'max': round(float(values.max()), 2),
                'q25': round(float(np.percentile(values, 25)), 2),
                'q75': round(float(np.percentile(values, 75)), 2),
                'variance': round(float(values.var()), 2),
                'range': round(float(values.max() - values.min()), 2)
            }
        
        # Status distribution
        status_distribution = df['overall_status'].value_counts().to_dict()
        
        return jsonify({
            'statistics': statistics,
            'status_distribution': status_distribution,
            'total_readings': len(readings),
            'period': f'Last {days} days'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Statistical analysis failed', 'message': str(e)}), 500
