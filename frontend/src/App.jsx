import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useNavigate, useLocation } from 'react-router-dom';
import { Toaster, toast } from 'react-hot-toast';
import io from 'socket.io-client';

// Auth Context
const AuthContext = createContext(null);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    if (token && userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const response = await fetch('http://localhost:5001/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        setUser(data.user);
        toast.success('Login successful!');
        return { success: true };
      } else {
        toast.error(data.error || 'Login failed');
        return { success: false, error: data.error };
      }
    } catch (error) {
      toast.error('Connection error');
      return { success: false, error: 'Connection error' };
    }
  };

  const register = async (formData) => {
    try {
      const response = await fetch('http://localhost:5001/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        setUser(data.user);
        toast.success('Registration successful!');
        return { success: true };
      } else {
        toast.error(data.error || 'Registration failed');
        return { success: false, error: data.error };
      }
    } catch (error) {
      toast.error('Connection error');
      return { success: false, error: 'Connection error' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    toast.success('Logged out successfully');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => useContext(AuthContext);

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="flex items-center justify-center h-screen">
      <div className="spinner"></div>
    </div>;
  }
  
  if (!user) {
    return <Navigate to="/login" />;
  }
  
  return children;
};

// Navigation Component
const Navbar = () => {
  const { user, logout } = useAuth();
  const [showMenu, setShowMenu] = useState(false);
  const navigate = useNavigate();

  if (!user) return null;

  return (
    <nav className="glass sticky top-0 z-50 border-b border-white/20">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-3xl">🌊</span>
            <span className="text-2xl font-bold bg-gradient-to-r from-primary-500 to-cyan-500 bg-clip-text text-transparent">
              AquaPulse
            </span>
            <span className="badge bg-primary-100 text-primary-700 text-xs">AI-Powered</span>
          </Link>
          
          <div className="hidden md:flex items-center space-x-6">
            <NavLink to="/">Dashboard</NavLink>
            <NavLink to="/monitoring">Monitoring</NavLink>
            <NavLink to="/analytics">Analytics</NavLink>
            <NavLink to="/compliance">Compliance</NavLink>
            <NavLink to="/citizen">Citizen Portal</NavLink>
            <NavLink to="/settings">Settings</NavLink>
          </div>

          <div className="relative">
            <button 
              onClick={() => setShowMenu(!showMenu)}
              className="flex items-center space-x-2 glass px-4 py-2 rounded-xl hover:bg-white/90"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-cyan-500 rounded-full flex items-center justify-center text-white font-bold">
                {user.full_name.charAt(0)}
              </div>
              <span className="hidden md:block font-semibold">{user.full_name}</span>
              <span className="badge-success">{user.role}</span>
            </button>
            
            {showMenu && (
              <div className="absolute right-0 mt-2 w-48 glass rounded-xl shadow-2xl py-2">
                <Link to="/settings" className="block px-4 py-2 hover:bg-white/50 transition">
                  ⚙️ Settings
                </Link>
                <button onClick={logout} className="w-full text-left px-4 py-2 hover:bg-red-50 text-red-600 transition">
                  🚪 Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

const NavLink = ({ to, children }) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  
  return (
    <Link 
      to={to}
      className={`px-3 py-2 rounded-lg font-medium transition ${
        isActive 
          ? 'bg-primary-500 text-white' 
          : 'text-gray-700 dark:text-gray-200 hover:bg-white/50'
      }`}
    >
      {children}
    </Link>
  );
};

// Login Page
const LoginPage = () => {
  const [email, setEmail] = useState('admin@aquapulse.com');
  const [password, setPassword] = useState('Admin@123456');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const result = await login(email, password);
    setLoading(false);
    if (result.success) {
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-primary-500 via-cyan-500 to-blue-600">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-1/2 -left-1/4 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-float"></div>
        <div className="absolute -bottom-1/2 -right-1/4 w-96 h-96 bg-cyan-300/10 rounded-full blur-3xl animate-float" style={{animationDelay: '1s'}}></div>
      </div>
      
      <div className="card w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="text-6xl mb-4 animate-float">🌊</div>
          <h1 className="text-3xl font-bold mb-2">Welcome to AquaPulse</h1>
          <p className="text-gray-600 dark:text-gray-400">AI-Powered Water Quality Monitoring</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-semibold mb-2">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              placeholder="admin@aquapulse.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              placeholder="••••••••"
              required
            />
          </div>

          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center">
              <input type="checkbox" className="mr-2" />
              <span>Remember me</span>
            </label>
            <a href="#" className="text-primary-500 hover:underline">Forgot password?</a>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>

          <p className="text-center text-sm">
            Don't have an account? 
            <Link to="/register" className="text-primary-500 hover:underline ml-1">Register here</Link>
          </p>
        </form>

        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-center text-gray-500">
            Demo credentials: admin@aquapulse.com / Admin@123456
          </p>
        </div>
      </div>
    </div>
  );
};

// Register Page
const RegisterPage = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'citizen',
    phone: '',
    organization: ''
  });
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const result = await register(formData);
    setLoading(false);
    if (result.success) {
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-cyan-500 via-blue-500 to-primary-600">
      <div className="card w-full max-w-2xl">
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">📝</div>
          <h1 className="text-3xl font-bold mb-2">Create Account</h1>
          <p className="text-gray-600 dark:text-gray-400">Join AquaPulse for water quality monitoring</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-2">Full Name</label>
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                className="input"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="input"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Password</label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="input"
                required
                minLength={8}
              />
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Role</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({...formData, role: e.target.value})}
                className="input"
              >
                <option value="citizen">Citizen</option>
                <option value="government">Government Official</option>
                <option value="admin">Administrator</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Phone (Optional)</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                className="input"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Organization (Optional)</label>
              <input
                type="text"
                value={formData.organization}
                onChange={(e) => setFormData({...formData, organization: e.target.value})}
                className="input"
              />
            </div>
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Creating Account...' : 'Register'}
          </button>

          <p className="text-center text-sm">
            Already have an account? 
            <Link to="/login" className="text-primary-500 hover:underline ml-1">Login here</Link>
          </p>
        </form>
      </div>
    </div>
  );
};

// Dashboard Page - Main page with all features
const DashboardPage = () => {
  const [stats, setStats] = useState({ readings_today: 0, active_alerts: 0, compliance_score: 100, last_event: 'N/A' });
  const [parameters, setParameters] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [overallStatus, setOverallStatus] = useState('Safe');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const socket = io('http://localhost:5001');
    
    socket.on('new_reading', (data) => {
      updateDashboardWithReading(data);
    });

    socket.on('new_alert', (alert) => {
      setAlerts(prev => [alert, ...prev].slice(0, 10));
      toast.error(alert.message);
    });

    return () => socket.disconnect();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statusRes, alertsRes, latestRes] = await Promise.all([
        fetch('http://localhost:5001/api/status'),
        fetch('http://localhost:5001/api/alerts'),
        fetch('http://localhost:5001/api/latest')
      ]);

      const statusData = await statusRes.json();
      const alertsData = await alertsRes.json();
      const latestData = await latestRes.json();

      setStats({
        readings_today: statusData.readings_count || 0,
        active_alerts: statusData.active_alerts || 0,
        compliance_score: statusData.compliance_score || '100%',
        last_event: statusData.last_reading || 'N/A'
      });

      if (alertsData.length) {
        setAlerts(alertsData.slice(0, 10));
      }

      if (latestData.parameters) {
        updateDashboardWithReading(latestData);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const updateDashboardWithReading = (data) => {
    if (data.parameters) {
      const params = [
        { name: 'pH Level', value: data.parameters.pH, unit: '', safe: [6.5, 8.5], icon: '🧪', status: data.status?.pH || 'safe' },
        { name: 'TDS', value: data.parameters.tds, unit: 'ppm', safe: [0, 500], icon: '💧', status: data.status?.tds || 'safe' },
        { name: 'Turbidity', value: data.parameters.turbidity, unit: 'NTU', safe: [0, 5], icon: '🌫️', status: data.status?.turbidity || 'safe' },
        { name: 'Temperature', value: data.parameters.temperature, unit: '°C', safe: [15, 35], icon: '🌡️', status: data.status?.temperature || 'safe' },
        { name: 'Conductivity', value: data.parameters.conductivity, unit: 'µS/cm', safe: [0, 1000], icon: '⚡', status: data.status?.conductivity || 'safe' },
        { name: 'Dissolved Oxygen', value: data.parameters.dissolved_oxygen, unit: 'mg/L', safe: [5, 14], icon: '🫧', status: data.status?.dissolved_oxygen || 'safe' }
      ];
      setParameters(params);
      setOverallStatus(data.overall_status || 'Safe');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><div className="spinner"></div></div>;
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      
      <div className="container mx-auto px-4 py-8">
        {/* Status Banner */}
        <div className={`card mb-8 ${
          overallStatus === 'Safe' ? 'bg-gradient-to-r from-green-400/20 to-emerald-400/20' :
          overallStatus === 'Caution' ? 'bg-gradient-to-r from-yellow-400/20 to-orange-400/20' :
          'bg-gradient-to-r from-red-400/20 to-pink-400/20'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-6xl">
                {overallStatus === 'Safe' ? '✅' : overallStatus === 'Caution' ? '⚠️' : '🚨'}
              </div>
              <div>
                <h2 className="text-3xl font-bold mb-2">Water Quality: {overallStatus}</h2>
                <p className="text-gray-600 dark:text-gray-400">
                  {overallStatus === 'Safe' ? 'All parameters within safe limits' :
                   overallStatus === 'Caution' ? 'Some parameters need attention' :
                   'Immediate action required'}
                </p>
              </div>
            </div>
            <div className={`badge ${
              overallStatus === 'Safe' ? 'badge-success' :
              overallStatus === 'Caution' ? 'badge-warning' :
              'badge-danger'
            } text-lg px-6 py-3`}>
              {overallStatus.toUpperCase()}
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard icon="📊" title="Readings Today" value={stats.readings_today} color="blue" />
          <StatCard icon="🔔" title="Active Alerts" value={stats.active_alerts} color="red" pulse={stats.active_alerts > 0} />
          <StatCard icon="📈" title="Compliance Score" value={stats.compliance_score} color="green" />
          <StatCard icon="🕐" title="Last Update" value="Just now" color="purple" />
        </div>

        {/* Parameter Cards */}
        <div className="mb-8">
          <h3 className="text-2xl font-bold mb-4">Water Quality Parameters</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {parameters.map((param, idx) => (
              <ParameterCard key={idx} param={param} />
            ))}
          </div>
        </div>

        {/* Alerts Feed */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-2xl font-bold">Recent Alerts</h3>
            <button onClick={() => setAlerts([])} className="btn-secondary text-sm">
              Clear All
            </button>
          </div>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {alerts.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No alerts</p>
            ) : (
              alerts.map((alert, idx) => (
                <div key={idx} className="glass p-4 rounded-xl flex items-start space-x-3">
                  <span className="text-2xl">
                    {alert.severity === 'critical' ? '🚨' : alert.severity === 'warning' ? '⚠️' : 'ℹ️'}
                  </span>
                  <div className="flex-1">
                    <p className="font-semibold">{alert.message}</p>
                    <p className="text-sm text-gray-500">{alert.timestamp}</p>
                  </div>
                  <span className={`badge ${
                    alert.severity === 'critical' ? 'badge-danger' : 'badge-warning'
                  }`}>
                    {alert.severity}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ icon, title, value, color, pulse }) => (
  <div className="card">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{title}</p>
        <p className="text-3xl font-bold">{value}</p>
      </div>
      <div className={`text-4xl ${pulse ? 'animate-bounce-slow' : ''}`}>{icon}</div>
    </div>
  </div>
);

const ParameterCard = ({ param }) => {
  const getStatusColor = () => {
    switch(param.status) {
      case 'safe': return 'border-green-400 bg-green-50/50 dark:bg-green-900/10';
      case 'warning': return 'border-yellow-400 bg-yellow-50/50 dark:bg-yellow-900/10';
      case 'danger': return 'border-red-400 bg-red-50/50 dark:bg-red-900/10';
      default: return 'border-gray-300';
    }
  };

  return (
    <div className={`card border-l-4 ${getStatusColor()}`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-2xl">{param.icon}</span>
            <h4 className="font-semibold">{param.name}</h4>
          </div>
          <div className="text-3xl font-bold">
            {param.value} <span className="text-lg text-gray-500">{param.unit}</span>
          </div>
        </div>
        <span className={`badge ${
          param.status === 'safe' ? 'badge-success' :
          param.status === 'warning' ? 'badge-warning' :
          'badge-danger'
        }`}>
          {param.status === 'safe' ? '✅ Safe' :
           param.status === 'warning' ? '⚠️ Warning' :
           '🚨 Danger'}
        </span>
      </div>
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Safe range: {param.safe[0]} - {param.safe[1]} {param.unit}
      </div>
    </div>
  );
};

// Simplified pages for other routes (you can expand these)
const MonitoringPage = () => (
  <div className="min-h-screen">
    <Navbar />
    <div className="container mx-auto px-4 py-8">
      <div className="card">
        <h1 className="text-3xl font-bold mb-4">📊 Real-Time Monitoring</h1>
        <p className="text-gray-600 mb-4">View all water quality readings and manage monitoring nodes</p>
        <div className="glass p-8 rounded-xl text-center">
          <div className="text-6xl mb-4">🗺️</div>
          <p className="text-lg">Interactive monitoring table and map will be displayed here</p>
          <p className="text-sm text-gray-500 mt-2">Feature: Data table, Map view, Node management</p>
        </div>
      </div>
    </div>
  </div>
);

const AnalyticsPage = () => (
  <div className="min-h-screen">
    <Navbar />
    <div className="container mx-auto px-4 py-8">
      <div className="card">
        <h1 className="text-3xl font-bold mb-4">🤖 AI Analytics</h1>
        <p className="text-gray-600 mb-4">LSTM forecasting, anomaly detection, and predictive maintenance</p>
        <div className="glass p-8 rounded-xl text-center">
          <div className="text-6xl mb-4">📈</div>
          <p className="text-lg">AI-powered analytics and predictions will be displayed here</p>
          <p className="text-sm text-gray-500 mt-2">Feature: 24-hour forecast, Anomaly detection, Trend analysis</p>
        </div>
      </div>
    </div>
  </div>
);

const CompliancePage = () => (
  <div className="min-h-screen">
    <Navbar />
    <div className="container mx-auto px-4 py-8">
      <div className="card">
        <h1 className="text-3xl font-bold mb-4">📋 Compliance & Reports</h1>
        <p className="text-gray-600 mb-4">CPCB BIS 10500:2012 compliance reports and automated reporting</p>
        <div className="glass p-8 rounded-xl text-center">
          <div className="text-6xl mb-4">📄</div>
          <p className="text-lg">CPCB report generator and compliance dashboard will be here</p>
          <p className="text-sm text-gray-500 mt-2">Feature: Report generation, Compliance scoring, Alert history</p>
        </div>
      </div>
    </div>
  </div>
);

const CitizenPortalPage = () => (
  <div className="min-h-screen">
    <Navbar />
    <div className="container mx-auto px-4 py-8">
      <div className="card">
        <h1 className="text-3xl font-bold mb-4">👥 Citizen Portal</h1>
        <p className="text-gray-600 mb-4">Public water quality information and issue reporting</p>
        <div className="glass p-8 rounded-xl text-center">
          <div className="text-6xl mb-4">🗣️</div>
          <p className="text-lg">Public dashboard and issue reporting form will be here</p>
          <p className="text-sm text-gray-500 mt-2">Feature: Public dashboard, Issue reporting, Educational resources</p>
        </div>
      </div>
    </div>
  </div>
);

const SettingsPage = () => (
  <div className="min-h-screen">
    <Navbar />
    <div className="container mx-auto px-4 py-8">
      <div className="card">
        <h1 className="text-3xl font-bold mb-4">⚙️ Settings & Administration</h1>
        <p className="text-gray-600 mb-4">System configuration and user management</p>
        <div className="glass p-8 rounded-xl text-center">
          <div className="text-6xl mb-4">🔧</div>
          <p className="text-lg">System settings and administration panel will be here</p>
          <p className="text-sm text-gray-500 mt-2">Feature: Alert thresholds, User management, Node configuration</p>
        </div>
      </div>
    </div>
  </div>
);

// Main App Component
function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
            <Route path="/monitoring" element={<ProtectedRoute><MonitoringPage /></ProtectedRoute>} />
            <Route path="/analytics" element={<ProtectedRoute><AnalyticsPage /></ProtectedRoute>} />
            <Route path="/compliance" element={<ProtectedRoute><CompliancePage /></ProtectedRoute>} />
            <Route path="/citizen" element={<ProtectedRoute><CitizenPortalPage /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
          </Routes>
          <Toaster position="top-right" />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
