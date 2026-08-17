from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import time
import json
import threading
from datetime import datetime
import pandas as pd
import numpy as np

from data_simulator import simulator
from ai_model import detector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aquapulse-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store historical data
historical_data = []
MAX_HISTORY = 100

# Store alert history
alert_history = []
MAX_ALERTS = 50

# ========== BACKGROUND DATA GENERATION ==========
def generate_data():
    """Background thread to generate simulated sensor data"""
    while True:
        try:
            reading = simulator.get_sensor_data()
            is_anomaly = detector.predict(reading)
            reading['is_anomaly'] = is_anomaly
            
            historical_data.append(reading)
            if len(historical_data) > MAX_HISTORY:
                historical_data.pop(0)
            
            # Emit via WebSocket
            socketio.emit('new_reading', reading)
            
            # Check for alerts
            if is_anomaly or reading['overall_status'] == 'Unsafe':
                alert = {
                    'timestamp': reading['timestamp'],
                    'message': '🚨 Contamination Detected!' if reading['overall_status'] == 'Unsafe' else '⚠️ Anomaly Detected',
                    'severity': 'critical' if reading['overall_status'] == 'Unsafe' else 'warning',
                    'parameters': reading['parameters'],
                    'status': reading['overall_status']
                }
                alert_history.append(alert)
                if len(alert_history) > MAX_ALERTS:
                    alert_history.pop(0)
                socketio.emit('new_alert', alert)
            
            time.sleep(1)  # 1 second between readings
            
        except Exception as e:
            print(f"Error generating data: {e}")
            time.sleep(1)

# ========== ROUTES ==========

@app.route('/')
def index():
    """Serve the dashboard"""
    return render_template('dashboard.html')

@app.route('/api/latest')
def get_latest():
    """Get the latest reading"""
    if historical_data:
        return jsonify(historical_data[-1])
    return jsonify({'error': 'No data available'})

@app.route('/api/history')
def get_history():
    """Get historical data for charts"""
    if historical_data:
        history = []
        for record in historical_data:
            entry = {
                'timestamp': record['timestamp'],
                'overall_status': record['overall_status']
            }
            entry.update(record['parameters'])
            history.append(entry)
        return jsonify(history)
    return jsonify([])

@app.route('/api/parameters')
def get_parameters():
    """Get parameter definitions"""
    return jsonify({
        'pH': {
            'label': 'pH Level', 
            'unit': '', 
            'min': 6.5, 
            'max': 8.5,
            'safe_min': 6.5,
            'safe_max': 8.5,
            'icon': '🧪'
        },
        'tds': {
            'label': 'Total Dissolved Solids', 
            'unit': 'ppm', 
            'min': 0, 
            'max': 500,
            'safe_min': 0,
            'safe_max': 500,
            'icon': '💧'
        },
        'turbidity': {
            'label': 'Turbidity', 
            'unit': 'NTU', 
            'min': 0, 
            'max': 5,
            'safe_min': 0,
            'safe_max': 5,
            'icon': '🌫️'
        },
        'temperature': {
            'label': 'Temperature', 
            'unit': '°C', 
            'min': 15, 
            'max': 35,
            'safe_min': 15,
            'safe_max': 35,
            'icon': '🌡️'
        },
        'conductivity': {
            'label': 'Conductivity', 
            'unit': 'µS/cm', 
            'min': 0, 
            'max': 1000,
            'safe_min': 0,
            'safe_max': 1000,
            'icon': '⚡'
        },
        'dissolved_oxygen': {
            'label': 'Dissolved Oxygen', 
            'unit': 'mg/L', 
            'min': 5, 
            'max': 14,
            'safe_min': 5,
            'safe_max': 14,
            'icon': '🫧'
        }
    })

@app.route('/api/generate_report')
def generate_report():
    """Generate a CPCB-aligned compliance report"""
    if not historical_data:
        return jsonify({'error': 'No data available'})
    
    latest = historical_data[-1]
    
    # Calculate statistics for each parameter
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'latest_reading': latest,
        'total_readings': len(historical_data),
        'parameters': {},
        'alert_count': len(alert_history),
        'compliance_status': latest['overall_status'],
        'anomaly_detected': latest.get('is_anomaly', False),
        'report_id': f"AQP-{datetime.now().strftime('%Y%m%d')}-{str(len(historical_data)).zfill(4)}"
    }
    
    # CPCB BIS 10500:2012 standards
    cpcb_standards = {
        'pH': {'min': 6.5, 'max': 8.5, 'unit': ''},
        'tds': {'min': 0, 'max': 500, 'unit': 'ppm'},
        'turbidity': {'min': 0, 'max': 5, 'unit': 'NTU'},
        'temperature': {'min': 15, 'max': 35, 'unit': '°C'},
        'conductivity': {'min': 0, 'max': 1000, 'unit': 'µS/cm'},
        'dissolved_oxygen': {'min': 5, 'max': 14, 'unit': 'mg/L'}
    }
    
    for param in ['pH', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen']:
        values = [record['parameters'][param] for record in historical_data]
        current = values[-1]
        
        # Check compliance against CPCB standards
        standard = cpcb_standards[param]
        is_compliant = standard['min'] <= current <= standard['max']
        
        report_data['parameters'][param] = {
            'current': current,
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'avg': round(sum(values) / len(values), 2),
            'std_dev': round(np.std(values), 2),
            'unit': standard['unit'],
            'cpcb_min': standard['min'],
            'cpcb_max': standard['max'],
            'is_compliant': is_compliant
        }
    
    # Overall compliance score
    compliant_count = sum(1 for p in report_data['parameters'].values() if p['is_compliant'])
    report_data['compliance_score'] = round((compliant_count / 6) * 100, 2)
    
    return jsonify(report_data)

@app.route('/api/reports')
def get_reports():
    """Get list of generated reports"""
    # For demo, return a list of recent reports
    reports = []
    for i, record in enumerate(historical_data[-10:]):
        reports.append({
            'id': f"AQP-{datetime.now().strftime('%Y%m%d')}-{str(i).zfill(4)}",
            'timestamp': record['timestamp'],
            'status': record['overall_status'],
            'readings': len(historical_data)
        })
    return jsonify(reports)

@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify({
        'status': 'online',
        'readings_count': len(historical_data),
        'alert_count': len(alert_history),
        'last_reading': historical_data[-1]['timestamp'] if historical_data else None,
        'system_uptime': 'Active',
        'hardware_nodes': 1,
        'active_alerts': len([a for a in alert_history if a['severity'] == 'critical']),
        'compliance_score': '100%' if len(historical_data) > 0 else 'N/A'
    })

@app.route('/api/alerts')
def get_alerts():
    """Get all alerts"""
    return jsonify(alert_history)

@app.route('/api/alert/<alert_id>', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert"""
    return jsonify({'status': 'success', 'message': f'Alert {alert_id} resolved'})

@app.route('/api/simulate_contamination', methods=['POST'])
def simulate_contamination():
    """Force a contamination event for demonstration"""
    global simulator
    try:
        # Set contamination values
        simulator.contamination_event = True
        simulator.event_counter = 0
        simulator.current_values['pH'] = 4.8  # Acidic
        simulator.current_values['turbidity'] = 22.5  # Very turbid
        simulator.current_values['tds'] = 950.0  # High TDS
        simulator.current_values['temperature'] = 28.0
        simulator.current_values['conductivity'] = 850.0
        simulator.current_values['dissolved_oxygen'] = 4.2  # Low DO
        
        # Force immediate reading
        reading = simulator.get_sensor_data()
        is_anomaly = detector.predict(reading)
        reading['is_anomaly'] = is_anomaly
        
        historical_data.append(reading)
        if len(historical_data) > MAX_HISTORY:
            historical_data.pop(0)
        
        socketio.emit('new_reading', reading)
        
        # Create alert
        alert = {
            'timestamp': reading['timestamp'],
            'message': '🚨 Contamination Simulated! pH/Turbidity/TDS out of range',
            'severity': 'critical',
            'parameters': reading['parameters'],
            'status': 'Unsafe'
        }
        alert_history.append(alert)
        if len(alert_history) > MAX_ALERTS:
            alert_history.pop(0)
        socketio.emit('new_alert', alert)
        
        return jsonify({
            'status': 'success', 
            'message': 'Contamination simulated successfully',
            'reading': reading
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/reset_system', methods=['POST'])
def reset_system():
    """Reset the system to normal state"""
    global simulator, historical_data, alert_history
    try:
        # Reset simulator
        simulator.contamination_event = False
        simulator.event_counter = 0
        simulator.current_values = {
            'pH': 7.2,
            'tds': 250,
            'turbidity': 1.5,
            'temperature': 25,
            'conductivity': 500,
            'dissolved_oxygen': 8.5
        }
        
        # Clear alerts
        alert_history = []
        
        # Keep last 10 historical records
        if len(historical_data) > 10:
            historical_data = historical_data[-10:]
        
        return jsonify({
            'status': 'success', 
            'message': 'System reset to normal state'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/health_check')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'readings': len(historical_data),
        'alerts': len(alert_history)
    })

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ========== START BACKGROUND THREAD ==========
data_thread = threading.Thread(target=generate_data)
data_thread.daemon = True
data_thread.start()

# ========== MAIN ==========
if __name__ == '__main__':
    print("=" * 70)
    print("🌊 AquaPulse - AI Water Quality Monitoring Platform")
    print("=" * 70)
    print("🚀 Server running at: http://localhost:5001")
    print("📡 WebSocket active for real-time updates")
    print("=" * 70)
    print("📋 API Endpoints:")
    print("   GET  /                 - Dashboard")
    print("   GET  /api/latest       - Latest reading")
    print("   GET  /api/history      - Historical data")
    print("   GET  /api/parameters   - Parameter definitions")
    print("   GET  /api/generate_report - CPCB compliance report")
    print("   GET  /api/reports      - List of reports")
    print("   GET  /api/status       - System status")
    print("   GET  /api/alerts       - All alerts")
    print("   POST /api/simulate_contamination - Simulate contamination")
    print("   POST /api/reset_system - Reset to normal")
    print("   GET  /api/health_check - Health check")
    print("=" * 70)
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 70)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)