// AquaPulse Dashboard JavaScript

let socket = null;
let readingCount = 0;
let alertCount = 0;
let isContamination = false;
let parameterHistory = {
    pH: [],
    tds: [],
    turbidity: [],
    temperature: [],
    conductivity: [],
    dissolved_oxygen: []
};
let timeHistory = [];

// ========== PARTICLES BACKGROUND ==========
function createParticles() {
    const container = document.getElementById('particles');
    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.width = (Math.random() * 4 + 2) + 'px';
        particle.style.height = particle.style.width;
        particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
        particle.style.animationDelay = (Math.random() * 10) + 's';
        particle.style.opacity = Math.random() * 0.3 + 0.1;
        container.appendChild(particle);
    }
}
createParticles();

// ========== SOCKET CONNECTION ==========
function initSocket() {
    socket = io('http://localhost:5001');
    
    socket.on('connect', function() {
        console.log('Connected to server');
        document.getElementById('system-status').textContent = '● Online';
        document.getElementById('system-status').className = 'status-badge online';
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        document.getElementById('system-status').textContent = '● Offline';
        document.getElementById('system-status').className = 'status-badge offline';
    });
    
    socket.on('new_reading', function(data) {
        updateDashboard(data);
    });
}

// ========== UPDATE DASHBOARD ==========
function updateDashboard(data) {
    readingCount++;
    document.getElementById('readings-count').textContent = readingCount;
    document.getElementById('last-update').textContent = 'Last update: ' + new Date(data.timestamp).toLocaleTimeString();
    
    updateOverallStatus(data);
    updateParameterCards(data);
    updateCharts(data);
    
    if (data.is_anomaly || data.overall_status === 'Unsafe') {
        addAlert(data);
    }
    
    document.getElementById('active-alerts').textContent = alertCount;
}

// ========== UPDATE OVERALL STATUS ==========
function updateOverallStatus(data) {
    const banner = document.getElementById('overall-status');
    const title = document.getElementById('status-title');
    const description = document.getElementById('status-description');
    const icon = document.querySelector('.status-icon');
    const badge = document.getElementById('status-badge-large');
    const complianceScore = document.getElementById('compliance-score');
    
    // Animate status change
    banner.style.animation = 'none';
    setTimeout(() => {
        banner.style.animation = 'fadeInUp 0.5s ease';
    }, 10);
    
    switch(data.overall_status) {
        case 'Safe':
            banner.className = 'status-banner safe';
            title.textContent = 'Water Quality: Safe';
            description.textContent = 'All parameters are within safe limits';
            icon.textContent = '✅';
            badge.textContent = 'SAFE';
            badge.style.background = '#0d7a0d';
            complianceScore.textContent = '100%';
            break;
        case 'Caution':
            banner.className = 'status-banner caution';
            title.textContent = 'Water Quality: Caution';
            description.textContent = '⚠️ Some parameters are approaching unsafe levels';
            icon.textContent = '⚠️';
            badge.textContent = 'CAUTION';
            badge.style.background = '#f39c12';
            complianceScore.textContent = '75%';
            break;
        case 'Unsafe':
            banner.className = 'status-banner unsafe';
            title.textContent = '🚨 Water Quality: UNSAFE';
            description.textContent = 'Immediate action required - contamination detected!';
            icon.textContent = '🚨';
            badge.textContent = 'UNSAFE';
            badge.style.background = '#c0392b';
            complianceScore.textContent = '0%';
            break;
    }
}

// ========== UPDATE PARAMETER CARDS ==========
function updateParameterCards(data) {
    const grid = document.getElementById('parameters-grid');
    
    if (grid.children.length === 0) {
        const params = ['pH', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen'];
        const labels = {
            'pH': 'pH Level',
            'tds': 'Total Dissolved Solids',
            'turbidity': 'Turbidity',
            'temperature': 'Temperature',
            'conductivity': 'Conductivity',
            'dissolved_oxygen': 'Dissolved Oxygen'
        };
        const units = {
            'pH': '',
            'tds': 'ppm',
            'turbidity': 'NTU',
            'temperature': '°C',
            'conductivity': 'µS/cm',
            'dissolved_oxygen': 'mg/L'
        };
        const ranges = {
            'pH': 'Safe: 6.5 - 8.5',
            'tds': 'Safe: < 500 ppm',
            'turbidity': 'Safe: < 5 NTU',
            'temperature': 'Safe: 15 - 35°C',
            'conductivity': 'Safe: < 1000 µS/cm',
            'dissolved_oxygen': 'Safe: > 5 mg/L'
        };
        const icons = {
            'pH': '🧪',
            'tds': '💧',
            'turbidity': '🌫️',
            'temperature': '🌡️',
            'conductivity': '⚡',
            'dissolved_oxygen': '🫧'
        };
        
        params.forEach(param => {
            const card = document.createElement('div');
            card.className = 'parameter-card';
            card.id = `card-${param}`;
            card.innerHTML = `
                <div class="param-label">${icons[param]} ${labels[param]}</div>
                <div class="param-value" id="value-${param}">--</div>
                <div class="param-unit">${units[param]}</div>
                <div class="param-status" id="status-${param}">--</div>
                <div class="param-range">${ranges[param]}</div>
            `;
            grid.appendChild(card);
        });
    }
    
    const params = ['pH', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen'];
    params.forEach(param => {
        const value = data.parameters[param];
        const valueEl = document.getElementById(`value-${param}`);
        const statusEl = document.getElementById(`status-${param}`);
        const card = document.getElementById(`card-${param}`);
        
        if (valueEl) {
            // Animate value change
            valueEl.style.transition = 'all 0.3s ease';
            valueEl.textContent = value;
        }
        
        if (statusEl) {
            const status = data.status[param] || 'safe';
            const statusLabels = {
                'safe': '✅ Safe',
                'warning': '⚠️ Warning',
                'danger': '🚨 Danger'
            };
            statusEl.textContent = statusLabels[status] || '--';
            statusEl.className = `param-status ${status}`;
        }
        
        if (card) {
            card.className = `parameter-card status-${status}`;
        }
    });
}

// ========== UPDATE CHARTS ==========
function updateCharts(data) {
    const params = ['pH', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen'];
    const time = new Date(data.timestamp).toLocaleTimeString();
    
    timeHistory.push(time);
    if (timeHistory.length > 20) timeHistory.shift();
    
    params.forEach(param => {
        parameterHistory[param].push(data.parameters[param]);
        if (parameterHistory[param].length > 20) parameterHistory[param].shift();
    });
    
    // Quality Chart - Multiple Parameters
    const colors = {
        'pH': '#2b6cb0',
        'tds': '#38a169',
        'turbidity': '#e53e3e',
        'temperature': '#d69e2e',
        'conductivity': '#805ad5',
        'dissolved_oxygen': '#00b5d8'
    };
    
    const traces = [];
    const displayParams = ['turbidity', 'pH', 'tds'];
    const displayLabels = {
        'turbidity': 'Turbidity (NTU)',
        'pH': 'pH Level',
        'tds': 'TDS (ppm)'
    };
    
    displayParams.forEach(param => {
        traces.push({
            type: 'scatter',
            mode: 'lines+markers',
            x: timeHistory,
            y: parameterHistory[param],
            name: displayLabels[param],
            line: { color: colors[param], width: 2 },
            marker: { size: 6 }
        });
    });
    
    const layout1 = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', size: 12 },
        margin: { l: 50, r: 20, t: 20, b: 50 },
        xaxis: { title: 'Time', showgrid: true, gridcolor: '#f0f4f8' },
        yaxis: { title: 'Value', showgrid: true, gridcolor: '#f0f4f8' },
        showlegend: true,
        legend: { orientation: 'h', y: 1.1 }
    };
    
    Plotly.react('quality-chart', traces, layout1);
    
    // Distribution Chart
    const distTrace = {
        type: 'bar',
        x: ['pH', 'TDS', 'Turbidity', 'Temp', 'Cond', 'DO'],
        y: [
            parameterHistory.pH[parameterHistory.pH.length - 1] || 0,
            parameterHistory.tds[parameterHistory.tds.length - 1] || 0,
            parameterHistory.turbidity[parameterHistory.turbidity.length - 1] || 0,
            parameterHistory.temperature[parameterHistory.temperature.length - 1] || 0,
            parameterHistory.conductivity[parameterHistory.conductivity.length - 1] || 0,
            parameterHistory.dissolved_oxygen[parameterHistory.dissolved_oxygen.length - 1] || 0
        ],
        marker: {
            color: ['#2b6cb0', '#38a169', '#e53e3e', '#d69e2e', '#805ad5', '#00b5d8']
        }
    };
    
    const layout2 = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', size: 12 },
        margin: { l: 50, r: 20, t: 20, b: 50 },
        yaxis: { showgrid: true, gridcolor: '#f0f4f8' }
    };
    
    Plotly.react('distribution-chart', [distTrace], layout2);
}

// ========== ADD ALERT ==========
function addAlert(data) {
    alertCount++;
    document.getElementById('active-alerts').textContent = alertCount;
    
    // Animate alert count
    const alertEl = document.getElementById('active-alerts');
    alertEl.style.animation = 'none';
    setTimeout(() => {
        alertEl.style.animation = 'pulse 0.5s ease';
    }, 10);
    
    const log = document.getElementById('alert-log');
    const emptyMsg = log.querySelector('.alert-log-empty');
    if (emptyMsg) emptyMsg.remove();
    
    const alertItem = document.createElement('div');
    alertItem.className = 'alert-item';
    const message = data.overall_status === 'Unsafe' ? '🚨 Contamination Detected!' : '⚠️ Anomaly Detected';
    const severity = data.overall_status === 'Unsafe' ? '#e53e3e' : '#f39c12';
    alertItem.style.borderLeftColor = severity;
    alertItem.innerHTML = `
        <span class="alert-message">${message}</span>
        <span class="alert-time">${new Date(data.timestamp).toLocaleTimeString()}</span>
    `;
    log.prepend(alertItem);
    
    while (log.children.length > 10) {
        log.removeChild(log.lastChild);
    }
}

// ========== GENERATE REPORT ==========
function generateReport() {
    fetch('/api/generate_report')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            const reportWindow = window.open('', '_blank', 'width=900,height=700');
            reportWindow.document.write(`
                <html>
                <head>
                    <title>AquaPulse - Compliance Report</title>
                    <style>
                        body { font-family: 'Inter', sans-serif; padding: 40px; max-width: 900px; margin: auto; }
                        h1 { color: #2b6cb0; border-bottom: 3px solid #2b6cb0; padding-bottom: 10px; }
                        .header { display: flex; justify-content: space-between; align-items: center; }
                        .status { padding: 12px 20px; border-radius: 8px; margin: 20px 0; font-weight: 700; }
                        .status.safe { background: #e6f7e6; color: #0d7a0d; }
                        .status.caution { background: #fff3cd; color: #856404; }
                        .status.unsafe { background: #fde8e8; color: #721c24; }
                        .param-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 20px 0; }
                        .param-card { background: #f7fafc; padding: 16px; border-radius: 8px; border-left: 4px solid #2b6cb0; }
                        .param-label { font-size: 12px; color: #718096; font-weight: 600; text-transform: uppercase; }
                        .param-value { font-size: 22px; font-weight: 700; margin: 4px 0; }
                        .param-stats { font-size: 12px; color: #718096; }
                        .footer { margin-top: 40px; padding-top: 20px; border-top: 2px solid #e2e8f0; font-size: 12px; color: #718096; text-align: center; }
                        .badge-cpcb { background: #2b6cb0; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>🌊 AquaPulse - Compliance Report</h1>
                        <span class="badge-cpcb">CPCB-Aligned</span>
                    </div>
                    <p><strong>Generated:</strong> ${new Date(data.timestamp).toLocaleString()}</p>
                    <p><strong>Total Readings:</strong> ${data.total_readings}</p>
                    
                    <div class="status ${data.compliance_status.toLowerCase()}">
                        <strong>Overall Compliance Status: ${data.compliance_status}</strong>
                        ${data.anomaly_detected ? ' ⚠️ Anomaly Detected!' : ''}
                    </div>
                    
                    <h3>📊 Parameter Summary</h3>
                    <div class="param-grid">
            `);
            
            const labels = {
                'pH': 'pH Level',
                'tds': 'TDS',
                'turbidity': 'Turbidity',
                'temperature': 'Temperature',
                'conductivity': 'Conductivity',
                'dissolved_oxygen': 'Dissolved Oxygen'
            };
            const units = {
                'pH': '',
                'tds': 'ppm',
                'turbidity': 'NTU',
                'temperature': '°C',
                'conductivity': 'µS/cm',
                'dissolved_oxygen': 'mg/L'
            };
            
            for (const [param, stats] of Object.entries(data.parameters)) {
                reportWindow.document.write(`
                    <div class="param-card">
                        <div class="param-label">${labels[param]}</div>
                        <div class="param-value">${stats.current} ${units[param]}</div>
                        <div class="param-stats">Min: ${stats.min} | Max: ${stats.max} | Avg: ${stats.avg}</div>
                    </div>
                `);
            }
            
            reportWindow.document.write(`
                    </div>
                    <div class="footer">
                        Generated by AquaPulse AI Water Quality Monitoring Platform<br>
                        © 2026 AquaPulse • IIT Bombay-Honeywell CE Future Skills & Innovation
                    </div>
                </body>
                </html>
            `);
            reportWindow.document.close();
        })
        .catch(error => {
            console.error('Error generating report:', error);
            alert('Error generating report');
        });
}

// ========== SIMULATE CONTAMINATION ==========
function simulateContamination() {
    fetch('/api/simulate_contamination', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log('Contamination simulated:', data);
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// ========== CLEAR ALERTS ==========
function clearAlerts() {
    alertCount = 0;
    document.getElementById('active-alerts').textContent = '0';
    document.getElementById('alert-log').innerHTML = `<div class="alert-log-empty">✅ No alerts detected</div>`;
}

// ========== INITIALIZE ==========
document.addEventListener('DOMContentLoaded', function() {
    initSocket();
    
    fetch('/api/history')
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                const latest = data[data.length - 1];
                const formattedData = {
                    timestamp: latest.timestamp,
                    parameters: {
                        pH: latest.pH || 0,
                        tds: latest.tds || 0,
                        turbidity: latest.turbidity || 0,
                        temperature: latest.temperature || 0,
                        conductivity: latest.conductivity || 0,
                        dissolved_oxygen: latest.dissolved_oxygen || 0
                    },
                    overall_status: latest.overall_status || 'Safe',
                    status: {
                        pH: latest.pH > 8.5 ? 'danger' : latest.pH > 7.5 ? 'warning' : 'safe',
                        tds: latest.tds > 500 ? 'danger' : latest.tds > 400 ? 'warning' : 'safe',
                        turbidity: latest.turbidity > 5 ? 'danger' : latest.turbidity > 3 ? 'warning' : 'safe',
                        temperature: latest.temperature > 35 ? 'danger' : latest.temperature > 30 ? 'warning' : 'safe',
                        conductivity: latest.conductivity > 1000 ? 'danger' : latest.conductivity > 800 ? 'warning' : 'safe',
                        dissolved_oxygen: latest.dissolved_oxygen < 5 ? 'danger' : latest.dissolved_oxygen < 6 ? 'warning' : 'safe'
                    },
                    is_anomaly: false
                };
                updateDashboard(formattedData);
            }
        })
        .catch(error => console.error('Error fetching initial data:', error));
    
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('readings-count').textContent = data.readings_count || 0;
        })
        .catch(error => console.error('Error fetching status:', error));
});