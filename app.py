from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import time, json, threading, uuid, random
from datetime import datetime, timedelta
import numpy as np

from data_simulator import simulator
from ai_model import detector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aquapulse-sih2026-secret'
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============================================================
# IN-MEMORY DATABASE
# ============================================================
USERS = [
    {'id': 1, 'email': 'admin@aquapulse.com',   'password': 'Admin@123456', 'full_name': 'Admin User',    'role': 'admin',      'organization': 'AquaPulse Team',          'status': 'active', 'last_login': '2026-08-18T00:00:00'},
    {'id': 2, 'email': 'govt@aquapulse.com',    'password': 'Govt@123456',  'full_name': 'Raj Patel',      'role': 'government', 'organization': 'Ministry of Jal Shakti',   'status': 'active', 'last_login': '2026-08-17T12:00:00'},
    {'id': 3, 'email': 'citizen@aquapulse.com', 'password': 'Citizen@123',  'full_name': 'Priya Sharma',   'role': 'citizen',    'organization': 'Public',                   'status': 'active', 'last_login': '2026-08-17T18:00:00'},
]

sessions = {}  # token -> user_id

MONITORING_NODES = [
    {'id': 1, 'name': 'Ahmedabad Main Station', 'location': 'Ahmedabad, Gujarat',  'lat': 23.0225, 'lng': 72.5714, 'type': 'Primary',   'status': 'active',      'battery': 87, 'last_seen': '2 mins ago',  'firmware': 'v2.1.4'},
    {'id': 2, 'name': 'Gandhinagar Canal',       'location': 'Gandhinagar, Gujarat','lat': 23.2156, 'lng': 72.6369, 'type': 'Secondary', 'status': 'active',      'battery': 72, 'last_seen': '5 mins ago',  'firmware': 'v2.1.3'},
    {'id': 3, 'name': 'Surat River Station',     'location': 'Surat, Gujarat',      'lat': 21.1702, 'lng': 72.8311, 'type': 'Primary',   'status': 'maintenance', 'battery': 45, 'last_seen': '25 mins ago', 'firmware': 'v2.0.9'},
]

citizen_issues = [
    {'id': 1, 'location': 'Ward 5, Ahmedabad',    'type': 'Color',  'description': 'Water appears yellowish in colour', 'status': 'resolved',    'submitted': '2026-08-16'},
    {'id': 2, 'location': 'Ward 12, Gandhinagar', 'type': 'Odor',   'description': 'Strong chlorine smell',             'status': 'in_progress', 'submitted': '2026-08-17'},
]

system_settings = {
    'thresholds': {
        'pH':               {'min': 6.5,  'max': 8.5},
        'tds':              {'min': 0,    'max': 500},
        'turbidity':        {'min': 0,    'max': 5},
        'temperature':      {'min': 15,   'max': 35},
        'conductivity':     {'min': 0,    'max': 1000},
        'dissolved_oxygen': {'min': 5,    'max': 14},
    },
    'sampling_interval':    3,
    'notifications':        {'email': True, 'sms': True, 'push': True},
    'data_retention_days':  365,
    'auto_report_daily':    True,
    'auto_report_weekly':   True,
    'auto_report_monthly':  True,
}

historical_data = []
MAX_HISTORY = 200

alert_history = []
MAX_ALERTS   = 100

# ============================================================
# AUTH HELPERS
# ============================================================
def generate_token(user_id):
    token = str(uuid.uuid4())
    sessions[token] = user_id
    return token

def safe_user(u):
    return {k: v for k, v in u.items() if k != 'password'}

# ============================================================
# BACKGROUND DATA THREAD
# ============================================================
def generate_data():
    while True:
        try:
            reading = simulator.get_sensor_data()
            is_anomaly = bool(detector.predict(reading))
            reading['is_anomaly'] = is_anomaly

            historical_data.append(reading)
            if len(historical_data) > MAX_HISTORY:
                historical_data.pop(0)

            socketio.emit('new_reading', reading)

            if is_anomaly or reading['overall_status'] == 'Unsafe':
                alert = {
                    'id':         str(uuid.uuid4())[:8],
                    'timestamp':  reading['timestamp'],
                    'message':    '🚨 Contamination Detected!' if reading['overall_status'] == 'Unsafe' else '⚠️ Anomaly Detected',
                    'severity':   'critical' if reading['overall_status'] == 'Unsafe' else 'warning',
                    'parameters': reading['parameters'],
                    'status':     reading['overall_status'],
                    'resolved':   False,
                }
                alert_history.append(alert)
                if len(alert_history) > MAX_ALERTS:
                    alert_history.pop(0)
                socketio.emit('new_alert', alert)

            time.sleep(1)
        except Exception as e:
            print(f"[DataThread] Error: {e}")
            time.sleep(1)

# ============================================================
# AUTH ROUTES
# ============================================================
@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data     = request.json or {}
    email    = data.get('email', '')
    password = data.get('password', '')
    user = next((u for u in USERS if u['email'] == email and u['password'] == password), None)
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401
    user['last_login'] = datetime.now().isoformat()
    token = generate_token(user['id'])
    return jsonify({'access_token': token, 'user': safe_user(user)})

@app.route('/api/auth/register', methods=['POST'])
def auth_register():
    data      = request.json or {}
    email     = data.get('email', '')
    password  = data.get('password', '')
    full_name = data.get('full_name', '')
    if not email or not password or not full_name:
        return jsonify({'error': 'Email, password and full name are required'}), 400
    if any(u['email'] == email for u in USERS):
        return jsonify({'error': 'Email already registered'}), 409
    new_user = {
        'id':           len(USERS) + 1,
        'email':        email,
        'password':     password,
        'full_name':    full_name,
        'role':         data.get('role', 'citizen'),
        'organization': data.get('organization', ''),
        'status':       'active',
        'last_login':   datetime.now().isoformat(),
    }
    USERS.append(new_user)
    token = generate_token(new_user['id'])
    return jsonify({'access_token': token, 'user': safe_user(new_user)}), 201

@app.route('/api/auth/me')
def auth_me():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = sessions.get(token)
    user = next((u for u in USERS if u['id'] == user_id), None) if user_id else None
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(safe_user(user))

# ============================================================
# CORE SENSOR ROUTES
# ============================================================
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/latest')
def get_latest():
    if historical_data:
        return jsonify(historical_data[-1])
    return jsonify({'error': 'No data available'})

@app.route('/api/history')
def get_history():
    limit = int(request.args.get('limit', 60))
    if historical_data:
        result = []
        for record in historical_data[-limit:]:
            entry = {'timestamp': record['timestamp'], 'overall_status': record['overall_status'], 'is_anomaly': record.get('is_anomaly', False)}
            entry.update(record['parameters'])
            result.append(entry)
        return jsonify(result)
    return jsonify([])

@app.route('/api/parameters')
def get_parameters():
    return jsonify({
        'pH':               {'label': 'pH Level',             'unit': '',      'safe_min': 6.5, 'safe_max': 8.5,  'icon': '🧪'},
        'tds':              {'label': 'Total Dissolved Solids','unit': 'ppm',   'safe_min': 0,   'safe_max': 500,  'icon': '💧'},
        'turbidity':        {'label': 'Turbidity',             'unit': 'NTU',   'safe_min': 0,   'safe_max': 5,    'icon': '🌫️'},
        'temperature':      {'label': 'Temperature',           'unit': '°C',    'safe_min': 15,  'safe_max': 35,   'icon': '🌡️'},
        'conductivity':     {'label': 'Conductivity',          'unit': 'µS/cm', 'safe_min': 0,   'safe_max': 1000, 'icon': '⚡'},
        'dissolved_oxygen': {'label': 'Dissolved Oxygen',      'unit': 'mg/L',  'safe_min': 5,   'safe_max': 14,   'icon': '🫧'},
    })

@app.route('/api/status')
def get_status():
    active_alerts = len([a for a in alert_history if a.get('severity') == 'critical' and not a.get('resolved')])
    return jsonify({
        'status':           'online',
        'readings_count':   len(historical_data),
        'alert_count':      len(alert_history),
        'last_reading':     historical_data[-1]['timestamp'] if historical_data else None,
        'system_uptime':    'Active',
        'hardware_nodes':   len(MONITORING_NODES),
        'active_alerts':    active_alerts,
        'compliance_score': '98.5%',
    })

@app.route('/api/alerts')
def get_alerts():
    return jsonify(alert_history)

@app.route('/api/alert/<alert_id>', methods=['POST'])
def resolve_alert(alert_id):
    for a in alert_history:
        if a.get('id') == alert_id:
            a['resolved'] = True
            break
    return jsonify({'status': 'success'})

# ============================================================
# REPORT GENERATION
# ============================================================
CPCB = {
    'pH':               {'min': 6.5,  'max': 8.5,  'unit': ''},
    'tds':              {'min': 0,    'max': 500,   'unit': 'ppm'},
    'turbidity':        {'min': 0,    'max': 5,     'unit': 'NTU'},
    'temperature':      {'min': 15,   'max': 35,    'unit': '°C'},
    'conductivity':     {'min': 0,    'max': 1000,  'unit': 'µS/cm'},
    'dissolved_oxygen': {'min': 5,    'max': 14,    'unit': 'mg/L'},
}

@app.route('/api/generate_report')
def generate_report():
    if not historical_data:
        return jsonify({'error': 'No data available'})
    latest = historical_data[-1]
    report = {
        'timestamp':         datetime.now().isoformat(),
        'report_id':         f"AQP-{datetime.now().strftime('%Y%m%d')}-{str(len(historical_data)).zfill(4)}",
        'total_readings':    len(historical_data),
        'parameters':        {},
        'alert_count':       len(alert_history),
        'compliance_status': latest['overall_status'],
    }
    for param, std in CPCB.items():
        vals    = [r['parameters'][param] for r in historical_data]
        current = vals[-1]
        report['parameters'][param] = {
            'current':    current,
            'min':        round(min(vals), 2),
            'max':        round(max(vals), 2),
            'avg':        round(sum(vals) / len(vals), 2),
            'std_dev':    round(float(np.std(vals)), 2),
            'unit':       std['unit'],
            'cpcb_min':   std['min'],
            'cpcb_max':   std['max'],
            'is_compliant': std['min'] <= current <= std['max'],
        }
    ok = sum(1 for p in report['parameters'].values() if p['is_compliant'])
    report['compliance_score'] = round((ok / 6) * 100, 2)
    return jsonify(report)

@app.route('/api/reports')
def get_reports():
    reports = []
    for i, rec in enumerate(historical_data[-10:]):
        reports.append({
            'id':       f"AQP-{datetime.now().strftime('%Y%m%d')}-{str(i).zfill(4)}",
            'timestamp': rec['timestamp'],
            'status':   rec['overall_status'],
            'readings': len(historical_data),
        })
    return jsonify(reports)

# ============================================================
# SIMULATION ROUTES
# ============================================================
@app.route('/api/simulate_contamination', methods=['POST'])
def simulate_contamination():
    global simulator
    try:
        simulator.contamination_event = True
        simulator.event_counter       = 0
        simulator.current_values.update({'pH': 4.8, 'turbidity': 22.5, 'tds': 950.0, 'temperature': 28.0, 'conductivity': 850.0, 'dissolved_oxygen': 4.2})
        reading    = simulator.get_sensor_data()
        is_anomaly = bool(detector.predict(reading))
        reading['is_anomaly'] = is_anomaly
        historical_data.append(reading)
        if len(historical_data) > MAX_HISTORY:
            historical_data.pop(0)
        socketio.emit('new_reading', reading)
        alert = {
            'id':         str(uuid.uuid4())[:8],
            'timestamp':  reading['timestamp'],
            'message':    '🚨 Contamination Simulated! pH/Turbidity/TDS critical',
            'severity':   'critical',
            'parameters': reading['parameters'],
            'status':     'Unsafe',
            'resolved':   False,
        }
        alert_history.append(alert)
        socketio.emit('new_alert', alert)
        return jsonify({'status': 'success', 'message': 'Contamination simulated', 'reading': reading})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/reset_system', methods=['POST'])
def reset_system():
    global historical_data, alert_history
    try:
        simulator.contamination_event = False
        simulator.event_counter       = 0
        simulator.current_values = {'pH': 7.2, 'tds': 250, 'turbidity': 1.5, 'temperature': 25, 'conductivity': 500, 'dissolved_oxygen': 8.5}
        alert_history = []
        if len(historical_data) > 10:
            historical_data = historical_data[-10:]
        return jsonify({'status': 'success', 'message': 'System reset to normal state'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ============================================================
# ANALYTICS (AI/ML mock data)
# ============================================================
@app.route('/api/analytics')
def get_analytics():
    now = datetime.now()

    def forecast(base, sigma, clamp_min, clamp_max):
        pts, v = [], base
        for i in range(24):
            v = max(clamp_min, min(clamp_max, v + random.gauss(0, sigma * 0.15)))
            lo = max(clamp_min, v - sigma * 0.6)
            hi = min(clamp_max, v + sigma * 0.6)
            pts.append({'time': (now + timedelta(hours=i)).strftime('%H:%M'), 'predicted': round(v, 2), 'lower': round(lo, 2), 'upper': round(hi, 2)})
        return pts

    curr = simulator.current_values if simulator else {'pH': 7.2, 'tds': 250, 'turbidity': 1.5, 'temperature': 25, 'conductivity': 500, 'dissolved_oxygen': 8.5}
    forecasts = {
        'pH':               forecast(curr.get('pH', 7.2),          0.15,  6.0, 9.0),
        'tds':              forecast(curr.get('tds', 250),          10,    50,  900),
        'turbidity':        forecast(curr.get('turbidity', 1.5),    0.4,   0,   20),
        'temperature':      forecast(curr.get('temperature', 25),   0.5,   15,  35),
        'dissolved_oxygen': forecast(curr.get('dissolved_oxygen', 8.5), 0.35, 2, 14),
        'conductivity':     forecast(curr.get('conductivity', 500), 20,    100, 1200),
    }

    anomalies = [
        {'id': 1, 'timestamp': (now - timedelta(hours=2)).isoformat(),  'parameter': 'pH',               'value': 5.8,  'score': 0.87, 'severity': 'high',     'resolved': True},
        {'id': 2, 'timestamp': (now - timedelta(hours=5)).isoformat(),  'parameter': 'turbidity',        'value': 8.2,  'score': 0.76, 'severity': 'medium',   'resolved': True},
        {'id': 3, 'timestamp': (now - timedelta(hours=12)).isoformat(), 'parameter': 'tds',              'value': 620,  'score': 0.65, 'severity': 'medium',   'resolved': False},
        {'id': 4, 'timestamp': (now - timedelta(days=1)).isoformat(),   'parameter': 'dissolved_oxygen', 'value': 3.5,  'score': 0.92, 'severity': 'critical', 'resolved': True},
    ]

    anomaly_frequency = [
        {'parameter': 'pH',          'count': 5, 'last_7_days': 2},
        {'parameter': 'TDS',         'count': 3, 'last_7_days': 1},
        {'parameter': 'Turbidity',   'count': 8, 'last_7_days': 3},
        {'parameter': 'Temperature', 'count': 2, 'last_7_days': 0},
        {'parameter': 'DO',          'count': 4, 'last_7_days': 2},
        {'parameter': 'Conductivity','count': 1, 'last_7_days': 0},
    ]

    maintenance = {
        'filter':  {'name': 'Water Filter',  'icon': '🔧', 'health': 73, 'last_maintenance': '2026-07-15', 'predicted_failure': '2026-10-20', 'recommendation': 'Schedule cleaning within 30 days',        'priority': 'medium'},
        'pump':    {'name': 'Main Pump',      'icon': '⚙️', 'health': 91, 'last_maintenance': '2026-08-01', 'predicted_failure': '2027-02-15', 'recommendation': 'Operating normally, next check in 6 months','priority': 'low'},
        'sensors': {'name': 'Sensor Array',   'icon': '📡', 'health': 58, 'last_maintenance': '2026-05-10', 'predicted_failure': '2026-09-05', 'recommendation': '⚠️ Calibration required within 2 weeks',   'priority': 'high'},
    }

    months     = ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    trend_data = [{'month': m, 'pH': round(7.1 + random.gauss(0, 0.15), 2), 'tds': round(240 + random.gauss(0, 12), 1), 'turbidity': round(1.4 + random.gauss(0, 0.25), 2), 'compliance': round(95 + random.gauss(0, 2.5), 1)} for m in months]

    metrics = {
        'pH':               {'rmse': 0.08, 'mae': 0.06, 'r2': 0.94},
        'tds':              {'rmse': 4.2,  'mae': 3.1,  'r2': 0.97},
        'turbidity':        {'rmse': 0.21, 'mae': 0.18, 'r2': 0.91},
        'temperature':      {'rmse': 0.15, 'mae': 0.12, 'r2': 0.98},
        'dissolved_oxygen': {'rmse': 0.19, 'mae': 0.15, 'r2': 0.93},
        'conductivity':     {'rmse': 8.3,  'mae': 6.7,  'r2': 0.96},
    }

    return jsonify({'forecasts': forecasts, 'anomalies': anomalies, 'anomaly_frequency': anomaly_frequency, 'maintenance': maintenance, 'trend_data': trend_data, 'metrics': metrics})

# ============================================================
# MONITORING NODES
# ============================================================
@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    return jsonify(MONITORING_NODES)

@app.route('/api/nodes', methods=['POST'])
def add_node():
    data = request.json or {}
    node = {
        'id':        len(MONITORING_NODES) + 1,
        'name':      data.get('name', 'New Node'),
        'location':  data.get('location', 'Unknown'),
        'lat':       float(data.get('lat', 0)),
        'lng':       float(data.get('lng', 0)),
        'type':      data.get('type', 'Secondary'),
        'status':    'active',
        'battery':   100,
        'last_seen': 'Just now',
        'firmware':  'v2.1.4',
    }
    MONITORING_NODES.append(node)
    return jsonify(node), 201

# ============================================================
# COMPLIANCE
# ============================================================
@app.route('/api/compliance/report')
def compliance_report():
    return generate_report().get_json() if historical_data else jsonify({'error': 'No data'})

# ============================================================
# CITIZEN PORTAL
# ============================================================
@app.route('/api/citizen/issues', methods=['GET'])
def get_issues():
    return jsonify(citizen_issues)

@app.route('/api/citizen/issues', methods=['POST'])
def submit_issue():
    data = request.json or {}
    issue = {
        'id':          len(citizen_issues) + 1,
        'location':    data.get('location', 'Unknown'),
        'type':        data.get('type', 'Other'),
        'description': data.get('description', ''),
        'status':      'pending',
        'submitted':   datetime.now().strftime('%Y-%m-%d'),
    }
    citizen_issues.append(issue)
    return jsonify(issue), 201

# ============================================================
# SETTINGS
# ============================================================
@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(system_settings)

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    data = request.json or {}
    system_settings.update(data)
    return jsonify({'status': 'success', 'settings': system_settings})

# ============================================================
# USER MANAGEMENT
# ============================================================
@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify([safe_user(u) for u in USERS])

@app.route('/api/users', methods=['POST'])
def add_user():
    data = request.json or {}
    user = {
        'id':           len(USERS) + 1,
        'email':        data.get('email', ''),
        'password':     data.get('password', 'TempPass@123'),
        'full_name':    data.get('full_name', ''),
        'role':         data.get('role', 'citizen'),
        'organization': data.get('organization', ''),
        'status':       'active',
        'last_login':   'Never',
    }
    USERS.append(user)
    return jsonify(safe_user(user)), 201

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    global USERS
    USERS = [u for u in USERS if u['id'] != user_id]
    return jsonify({'status': 'success'})

# ============================================================
# HEALTH CHECK
# ============================================================
@app.route('/api/health_check')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat(), 'readings': len(historical_data), 'alerts': len(alert_history)})

# ============================================================
# ERROR HANDLERS
# ============================================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================
# START BACKGROUND THREAD
# ============================================================
data_thread = threading.Thread(target=generate_data, daemon=True)
data_thread.start()

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print("=" * 65)
    print("🌊  AquaPulse — AI Water Quality Monitoring  (SIH 2026)")
    print("=" * 65)
    print("🚀  http://localhost:5001")
    print("=" * 65)
    print("🔐  Demo Credentials:")
    print("    Admin:   admin@aquapulse.com   /  Admin@123456")
    print("    Govt:    govt@aquapulse.com    /  Govt@123456")
    print("    Citizen: citizen@aquapulse.com /  Citizen@123")
    print("=" * 65)
    socketio.run(app, debug=True, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)