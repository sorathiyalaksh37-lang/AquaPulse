import React, {
  useState, useEffect, useRef, useMemo,
  createContext, useContext, useCallback
} from 'react';
import {
  BrowserRouter as Router, Routes, Route, Navigate,
  Link, useNavigate, useLocation
} from 'react-router-dom';
import { Toaster, toast } from 'react-hot-toast';
import { io } from 'socket.io-client';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area, ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, Cell
} from 'recharts';

const API = 'http://localhost:5001';

// ─────────────────────────────────────────────────────────────
// CONSTANTS
// ─────────────────────────────────────────────────────────────
const PARAMS = {
  pH:               { label: 'pH Level',             unit: '',      min: 6.5, max: 8.5,  icon: '🧪', color: '#3b82f6' },
  tds:              { label: 'TDS',                  unit: 'ppm',   min: 0,   max: 500,  icon: '💧', color: '#06b6d4' },
  turbidity:        { label: 'Turbidity',             unit: 'NTU',   min: 0,   max: 5,    icon: '🌫️', color: '#8b5cf6' },
  temperature:      { label: 'Temperature',           unit: '°C',    min: 15,  max: 35,   icon: '🌡️', color: '#f59e0b' },
  conductivity:     { label: 'Conductivity',          unit: 'µS/cm', min: 0,   max: 1000, icon: '⚡', color: '#10b981' },
  dissolved_oxygen: { label: 'Dissolved Oxygen',      unit: 'mg/L',  min: 5,   max: 14,   icon: '🫧', color: '#ef4444' },
};

const NAV = [
  { to: '/',           icon: '🏠', label: 'Dashboard'     },
  { to: '/monitoring', icon: '📊', label: 'Monitoring'    },
  { to: '/analytics',  icon: '🤖', label: 'AI Analytics'  },
  { to: '/compliance', icon: '📋', label: 'Compliance'    },
  { to: '/citizen',    icon: '👥', label: 'Citizen Portal' },
  { to: '/settings',   icon: '⚙️', label: 'Settings'      },
];

// ─────────────────────────────────────────────────────────────
// CONTEXTS
// ─────────────────────────────────────────────────────────────
const AuthCtx  = createContext(null);
const ThemeCtx = createContext(null);
const DataCtx  = createContext(null);

/* Auth */
const AuthProvider = ({ children }) => {
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const tok  = localStorage.getItem('aq_tok');
    const usr  = localStorage.getItem('aq_usr');
    if (tok && usr) { try { setUser(JSON.parse(usr)); } catch (_) {} }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const r = await fetch(`${API}/api/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const d = await r.json();
      if (r.ok) {
        localStorage.setItem('aq_tok', d.access_token);
        localStorage.setItem('aq_usr', JSON.stringify(d.user));
        setUser(d.user);
        toast.success(`Welcome, ${d.user.full_name}! 👋`);
        return { success: true };
      }
      toast.error(d.error || 'Login failed');
      return { success: false };
    } catch {
      toast.error('Cannot connect to server');
      return { success: false };
    }
  };

  const register = async (form) => {
    try {
      const r = await fetch(`${API}/api/auth/register`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const d = await r.json();
      if (r.ok) {
        localStorage.setItem('aq_tok', d.access_token);
        localStorage.setItem('aq_usr', JSON.stringify(d.user));
        setUser(d.user);
        toast.success('Account created! 🎉');
        return { success: true };
      }
      toast.error(d.error || 'Registration failed');
      return { success: false };
    } catch {
      toast.error('Cannot connect to server');
      return { success: false };
    }
  };

  const logout = () => {
    localStorage.removeItem('aq_tok');
    localStorage.removeItem('aq_usr');
    setUser(null);
    toast.success('Logged out');
  };

  return (
    <AuthCtx.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthCtx.Provider>
  );
};

/* Theme */
const ThemeProvider = ({ children }) => {
  const [dark, setDark] = useState(() => localStorage.getItem('aq_theme') !== 'light');
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('aq_theme', dark ? 'dark' : 'light');
  }, [dark]);
  return (
    <ThemeCtx.Provider value={{ dark, toggle: () => setDark(d => !d) }}>
      {children}
    </ThemeCtx.Provider>
  );
};

/* Live Data */
const DataProvider = ({ children }) => {
  const [reading,   setReading]   = useState(null);
  const [history,   setHistory]   = useState([]);
  const [alerts,    setAlerts]    = useState([]);
  const [sysStatus, setSysStatus] = useState({});
  const [connected, setConnected] = useState(false);
  const sockRef = useRef(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [lat, hist, alts, stat] = await Promise.all([
          fetch(`${API}/api/latest`).then(r => r.json()),
          fetch(`${API}/api/history`).then(r => r.json()),
          fetch(`${API}/api/alerts`).then(r => r.json()),
          fetch(`${API}/api/status`).then(r => r.json()),
        ]);
        if (lat?.parameters) setReading(lat);
        if (Array.isArray(hist)) setHistory(hist.slice(-60));
        if (Array.isArray(alts)) setAlerts(alts.slice(-30));
        if (stat?.status)        setSysStatus(stat);
      } catch (_) {}
    };
    load();

    const sock = io(API, { transports: ['websocket', 'polling'] });
    sockRef.current = sock;
    sock.on('connect',    ()  => setConnected(true));
    sock.on('disconnect', ()  => setConnected(false));
    sock.on('new_reading', d  => {
      setReading(d);
      setHistory(prev => {
        const e = { timestamp: d.timestamp, overall_status: d.overall_status, ...d.parameters };
        return [...prev.slice(-59), e];
      });
      setSysStatus(prev => ({ ...prev, readings_count: (prev.readings_count || 0) + 1 }));
    });
    sock.on('new_alert', a => {
      setAlerts(prev => [a, ...prev].slice(0, 40));
      toast.error(a.message, { duration: 6000, icon: a.severity === 'critical' ? '🚨' : '⚠️' });
    });
    return () => sock.disconnect();
  }, []);

  const clearAlerts = useCallback(() => setAlerts([]), []);

  return (
    <DataCtx.Provider value={{ reading, history, alerts, sysStatus, connected, clearAlerts }}>
      {children}
    </DataCtx.Provider>
  );
};

// ─────────────────────────────────────────────────────────────
// HOOKS
// ─────────────────────────────────────────────────────────────
const useAuth  = () => useContext(AuthCtx);
const useTheme = () => useContext(ThemeCtx);
const useData  = () => useContext(DataCtx);

// ─────────────────────────────────────────────────────────────
// UTILS
// ─────────────────────────────────────────────────────────────
const paramStatus = (key, val) => {
  const p = PARAMS[key]; if (!p) return 'safe';
  if (val < p.min || val > p.max) return 'danger';
  const lo = p.min + (p.max - p.min) * 0.05;
  const hi = p.max - (p.max - p.min) * 0.05;
  if (val < lo || val > hi) return 'warning';
  return 'safe';
};

const fmtTime = ts => { try { return new Date(ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }); } catch { return ''; } };
const fmtDate = ts => { try { return new Date(ts).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }); } catch { return ''; } };
const fmtVal  = (v, d = 2) => v !== undefined && v !== null ? Number(v).toFixed(d) : '—';

// ─────────────────────────────────────────────────────────────
// SHARED COMPONENTS
// ─────────────────────────────────────────────────────────────

const Spinner = ({ sm }) => <div className={`spinner${sm ? ' spinner-sm' : ''}`} />;

const LoadingScreen = () => (
  <div className="flex flex-col items-center justify-center h-screen bg-slate-950 gap-5">
    <span className="text-6xl animate-float">🌊</span>
    <Spinner />
    <p className="text-slate-500 text-sm">Loading AquaPulse…</p>
  </div>
);

const StatusBadge = ({ status, lg }) => {
  const map = {
    safe:        ['badge-success', '✅ Safe'],
    warning:     ['badge-warning', '⚠️ Warning'],
    danger:      ['badge-danger',  '🚨 Danger'],
    critical:    ['badge-danger',  '🚨 Critical'],
    active:      ['badge-success', '● Active'],
    maintenance: ['badge-warning', '🔧 Maint.'],
    inactive:    ['badge bg-slate-700 text-slate-400', '○ Inactive'],
    pending:     ['badge-warning', '⏳ Pending'],
    in_progress: ['badge-info',    '🔄 In Progress'],
    resolved:    ['badge-success', '✅ Resolved'],
    high:        ['badge-danger',  '⬆ High'],
    medium:      ['badge-warning', '⬆ Medium'],
    low:         ['badge-info',    '⬇ Low'],
    compliant:   ['badge-success', '✅ Compliant'],
  };
  const [cls, lbl] = map[status] || ['badge bg-slate-700 text-slate-400', status];
  return <span className={`${cls}${lg ? ' text-sm px-4 py-1.5' : ''}`}>{lbl}</span>;
};

const Modal = ({ open, onClose, title, children, lg }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className={`relative glass-heavy rounded-2xl p-6 w-full max-h-[88vh] overflow-y-auto animate-slide-up ${lg ? 'max-w-3xl' : 'max-w-lg'}`}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-bold text-slate-100">{title}</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-200 text-xl w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
};

const StatCard = ({ icon, label, value, sub, color = 'blue', pulse }) => {
  const cols = {
    blue:   'from-blue-500/15   to-blue-600/5   border-blue-500/20   text-blue-400',
    green:  'from-green-500/15  to-green-600/5  border-green-500/20  text-green-400',
    red:    'from-red-500/15    to-red-600/5    border-red-500/20    text-red-400',
    purple: 'from-purple-500/15 to-purple-600/5 border-purple-500/20 text-purple-400',
    amber:  'from-amber-500/15  to-amber-600/5  border-amber-500/20  text-amber-400',
    cyan:   'from-cyan-500/15   to-cyan-600/5   border-cyan-500/20   text-cyan-400',
  };
  return (
    <div className={`card border bg-gradient-to-br ${cols[color] || cols.blue}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-500 text-xs font-medium uppercase tracking-wider mb-1">{label}</p>
          <p className={`text-3xl font-bold ${pulse ? 'animate-pulse' : ''}`}>{value}</p>
          {sub && <p className="text-slate-600 text-xs mt-1">{sub}</p>}
        </div>
        <span className="text-3xl opacity-70">{icon}</span>
      </div>
    </div>
  );
};

/* SVG Sparkline */
const Sparkline = ({ data = [], color = '#3b82f6' }) => {
  if (!data || data.length < 2) return <div className="h-9 bg-white/3 rounded-lg" />;
  const min = Math.min(...data), max = Math.max(...data), rng = Math.max(max - min, 0.001);
  const W = 120, H = 36;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * W},${H - ((v - min) / rng) * H * 0.8 - H * 0.1}`).join(' ');
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" preserveAspectRatio="none">
      <polyline points={`0,${H} ${pts} ${W},${H}`} fill={`${color}20`} stroke="none" />
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};

/* Circular gauge (SVG) */
const Gauge = ({ value, color, size = 80 }) => {
  const r = 32, circ = 2 * Math.PI * r;
  const dash = (value / 100) * circ;
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg viewBox="0 0 80 80" className="w-full h-full -rotate-90">
        <circle cx="40" cy="40" r={r} fill="none" stroke="#1e293b" strokeWidth="8" />
        <circle cx="40" cy="40" r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 1s ease' }} />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-sm font-bold" style={{ color }}>{value}%</span>
      </div>
    </div>
  );
};

/* Recharts shared tooltip */
const ChartTip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-xl p-3 text-xs border border-white/10 shadow-xl">
      <p className="text-slate-400 mb-1.5">{label}</p>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2 mb-0.5">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-300">{p.name}:</span>
          <strong className="text-slate-100">{typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</strong>
        </div>
      ))}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// LAYOUT — SIDEBAR + TOPBAR
// ─────────────────────────────────────────────────────────────
const Sidebar = ({ onClose }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="sidebar">
      {/* Logo */}
      <div className="px-5 py-4 border-b border-white/5 flex-shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🌊</span>
          <div>
            <p className="font-black text-lg text-white leading-tight tracking-tight">AquaPulse</p>
            <p className="text-xs text-blue-400 font-medium">SIH 2026 · AI Platform</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, icon, label }) => {
          const active = location.pathname === to;
          return (
            <Link key={to} to={to} onClick={onClose}
              className={`sidebar-item ${active ? 'sidebar-active' : ''}`}>
              <span className="text-lg w-7 text-center flex-shrink-0">{icon}</span>
              <span className="flex-1">{label}</span>
              {active && <span className="w-1.5 h-5 bg-blue-400 rounded-full" />}
            </Link>
          );
        })}
      </nav>

      {/* User footer */}
      {user && (
        <div className="p-3 border-t border-white/5 flex-shrink-0">
          <div className="flex items-center gap-2.5 p-3 rounded-xl bg-white/5 mb-2">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
              {user.full_name?.charAt(0)}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-200 truncate">{user.full_name}</p>
              <p className="text-xs text-slate-500 capitalize">{user.role}</p>
            </div>
          </div>
          <button onClick={() => { logout(); navigate('/login'); onClose?.(); }}
            className="btn-danger btn-sm w-full flex items-center justify-center gap-1.5">
            🚪 Logout
          </button>
        </div>
      )}
    </div>
  );
};

const Topbar = ({ title, onMenu }) => {
  const { alerts, connected } = useData();
  const [notifOpen, setNotifOpen] = useState(false);
  const unread = alerts.filter(a => !a.resolved).length;

  return (
    <header className="h-16 border-b border-white/5 bg-slate-900/60 backdrop-blur-xl sticky top-0 z-30 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <button onClick={onMenu} className="lg:hidden text-slate-400 hover:text-slate-200 text-xl p-1">☰</button>
        <div>
          <h1 className="font-bold text-slate-100 text-lg leading-tight">{title}</h1>
          <p className="text-xs text-slate-600 hidden sm:block">
            {new Date().toLocaleDateString('en-IN', { weekday:'long', day:'numeric', month:'long', year:'numeric' })}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Live indicator */}
        <div className="hidden sm:flex items-center gap-1.5">
          <div className={`relative w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}>
            {connected && <span className="absolute inset-0 rounded-full bg-green-500 animate-ping opacity-60" />}
          </div>
          <span className="text-xs text-slate-500">{connected ? 'Live' : 'Offline'}</span>
        </div>

        {/* Notifications */}
        <div className="relative">
          <button onClick={() => setNotifOpen(o => !o)}
            className="relative p-2 rounded-xl hover:bg-white/5 text-slate-400 hover:text-slate-200 transition">
            🔔
            {unread > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full text-white text-[10px] flex items-center justify-center font-bold animate-pulse">
                {unread > 9 ? '9+' : unread}
              </span>
            )}
          </button>
          {notifOpen && (
            <div className="absolute right-0 top-12 w-80 glass-heavy rounded-2xl p-3 animate-slide-up z-50 shadow-2xl">
              <p className="text-xs font-semibold text-slate-400 px-2 mb-2 uppercase tracking-wider">Recent Alerts</p>
              <div className="space-y-1 max-h-60 overflow-y-auto">
                {alerts.length === 0
                  ? <p className="text-xs text-slate-600 text-center py-6">No alerts</p>
                  : alerts.slice(0, 8).map((a, i) => (
                    <div key={i} className="flex items-start gap-2 p-2 rounded-xl hover:bg-white/5">
                      <span className="text-base flex-shrink-0">{a.severity === 'critical' ? '🚨' : '⚠️'}</span>
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-slate-300 truncate">{a.message}</p>
                        <p className="text-[10px] text-slate-600">{fmtTime(a.timestamp)}</p>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>

        <div className="hidden md:flex items-center gap-1.5 bg-blue-500/10 border border-blue-500/20 rounded-xl px-3 py-1.5">
          <span className="text-blue-400 text-xs font-semibold">🏆 SIH 2026</span>
        </div>
      </div>
    </header>
  );
};

const Layout = ({ title, children }) => {
  const [sbOpen, setSbOpen] = useState(false);
  return (
    <div className="min-h-screen bg-slate-950">
      {/* Mobile sidebar overlay */}
      {sbOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setSbOpen(false)} />
          <Sidebar onClose={() => setSbOpen(false)} />
        </div>
      )}
      {/* Desktop sidebar */}
      <div className="hidden lg:block"><Sidebar onClose={() => {}} /></div>
      {/* Main */}
      <div className="lg:ml-64">
        <Topbar title={title} onMenu={() => setSbOpen(true)} />
        <main className="p-5 lg:p-6 animate-fade-in">{children}</main>
      </div>
    </div>
  );
};

const Guard = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <LoadingScreen />;
  if (!user)   return <Navigate to="/login" replace />;
  return children;
};

// ─────────────────────────────────────────────────────────────
// PAGE: LOGIN
// ─────────────────────────────────────────────────────────────
const LoginPage = () => {
  const [form,    setForm]    = useState({ email: '', password: '' });
  const [busy,    setBusy]    = useState(false);
  const [showPw,  setShowPw]  = useState(false);
  const { login, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => { if (user) navigate('/'); }, [user, navigate]);

  const submit = async e => {
    e.preventDefault();
    setBusy(true);
    const r = await login(form.email, form.password);
    setBusy(false);
    if (r.success) navigate('/');
  };

  const fill = (email, pw) => setForm({ email, password: pw });

  return (
    <div className="min-h-screen water-bg flex items-center justify-center p-4 relative">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl animate-float pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-cyan-600/10 rounded-full blur-3xl animate-float pointer-events-none" style={{ animationDelay: '2s' }} />

      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-7xl mb-4 inline-block animate-float">🌊</div>
          <h1 className="text-4xl font-black text-white tracking-tight">AquaPulse</h1>
          <p className="text-blue-300 text-sm mt-1">AI-Powered Water Quality Intelligence</p>
          <div className="inline-flex items-center gap-2 mt-3 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5">
            <span className="text-blue-400 text-xs font-semibold">🏆 Smart India Hackathon 2026</span>
          </div>
        </div>

        <div className="glass-heavy rounded-3xl p-8">
          <h2 className="text-xl font-bold text-slate-100 mb-6">Sign in to your account</h2>
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1.5">Email Address</label>
              <input id="login-email" type="email" required value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                className="input" placeholder="you@example.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1.5">Password</label>
              <div className="relative">
                <input id="login-password" type={showPw ? 'text' : 'password'} required value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  className="input pr-12" placeholder="••••••••" />
                <button type="button" onClick={() => setShowPw(s => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 text-sm">
                  {showPw ? '🙈' : '👁️'}
                </button>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input id="remember-me" type="checkbox" className="rounded accent-blue-500" />
                <span className="text-slate-400">Remember me</span>
              </label>
              <a href="#" className="text-blue-400 hover:text-blue-300 transition">Forgot password?</a>
            </div>
            <button id="login-btn" type="submit" disabled={busy}
              className="btn-primary w-full flex items-center justify-center gap-2 mt-1">
              {busy ? <><Spinner sm /> Signing in…</> : '🔑 Sign In'}
            </button>
          </form>

          <p className="text-center text-sm text-slate-500 mt-5">
            No account? <Link to="/register" className="text-blue-400 hover:text-blue-300">Register here</Link>
          </p>

          {/* Demo fills */}
          <div className="mt-6 pt-5 border-t border-white/5">
            <p className="text-[11px] text-slate-600 text-center mb-3 uppercase tracking-widest">Demo Quick Login</p>
            <div className="grid grid-cols-3 gap-2">
              {[
                { lbl: '🛡️ Admin',   e: 'admin@aquapulse.com',   p: 'Admin@123456' },
                { lbl: '🏛️ Govt',    e: 'govt@aquapulse.com',    p: 'Govt@123456' },
                { lbl: '👤 Citizen', e: 'citizen@aquapulse.com', p: 'Citizen@123' },
              ].map(c => (
                <button key={c.lbl} onClick={() => fill(c.e, c.p)}
                  className="btn-secondary btn-sm text-xs flex flex-col items-center py-2 gap-0.5">
                  {c.lbl}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// PAGE: REGISTER
// ─────────────────────────────────────────────────────────────
const RegisterPage = () => {
  const [form, setForm] = useState({ email:'', password:'', confirm:'', full_name:'', role:'citizen', organization:'', terms: false });
  const [busy, setBusy] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const strength = pw => {
    let s = 0;
    if (pw.length >= 8)        s++;
    if (/[A-Z]/.test(pw))      s++;
    if (/[0-9]/.test(pw))      s++;
    if (/[^A-Za-z0-9]/.test(pw)) s++;
    return s;
  };
  const sw = strength(form.password);
  const swLabel = ['Very Weak','Weak','Fair','Strong','Very Strong'][sw];
  const swColor = ['bg-red-500','bg-orange-500','bg-yellow-500','bg-green-500','bg-emerald-500'][sw];

  const submit = async e => {
    e.preventDefault();
    if (form.password !== form.confirm) return toast.error('Passwords do not match');
    if (!form.terms)  return toast.error('Please accept the terms');
    if (sw < 2)       return toast.error('Please use a stronger password');
    setBusy(true);
    const r = await register({ email: form.email, password: form.password, full_name: form.full_name, role: form.role, organization: form.organization });
    setBusy(false);
    if (r.success) navigate('/');
  };

  return (
    <div className="min-h-screen water-bg flex items-center justify-center p-4 relative">
      <div className="absolute top-1/3 right-1/4 w-72 h-72 bg-cyan-600/10 rounded-full blur-3xl animate-float pointer-events-none" />
      <div className="relative z-10 w-full max-w-2xl">
        <div className="text-center mb-7">
          <div className="text-5xl mb-3">📝</div>
          <h1 className="text-3xl font-black text-white">Create Account</h1>
          <p className="text-slate-400 mt-1 text-sm">Join AquaPulse — monitor water quality intelligently</p>
        </div>
        <div className="glass-heavy rounded-3xl p-8">
          <form onSubmit={submit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              {[['full_name','Full Name *','text'],['email','Email Address *','email'],['organization','Organization','text']].map(([k,l,t]) => (
                <div key={k} className={k === 'organization' ? '' : ''}>
                  <label className="block text-sm font-medium text-slate-400 mb-1.5">{l}</label>
                  <input type={t} value={form[k]} onChange={e => setForm(f => ({...f,[k]:e.target.value}))}
                    className="input" required={l.endsWith('*')} />
                </div>
              ))}
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1.5">Role *</label>
                <select value={form.role} onChange={e => setForm(f => ({...f, role: e.target.value}))} className="select">
                  <option value="citizen">Citizen</option>
                  <option value="government">Government Official</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1.5">Password *</label>
                <input type="password" value={form.password} onChange={e => setForm(f => ({...f, password: e.target.value}))}
                  className="input" required minLength={6} />
                {form.password && (
                  <div className="mt-2">
                    <div className="flex gap-1 mb-1">{[1,2,3,4].map(i => (
                      <div key={i} className={`h-1 flex-1 rounded-full transition-all ${sw >= i ? swColor : 'bg-white/10'}`} />
                    ))}</div>
                    <p className="text-xs text-slate-500">{swLabel}</p>
                  </div>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1.5">Confirm Password *</label>
                <input type="password" value={form.confirm} onChange={e => setForm(f => ({...f, confirm: e.target.value}))}
                  className="input" required />
                {form.confirm && form.password !== form.confirm &&
                  <p className="text-xs text-red-400 mt-1">Passwords don't match</p>}
              </div>
            </div>
            <label className="flex items-start gap-3 cursor-pointer mb-5">
              <input type="checkbox" checked={form.terms} onChange={e => setForm(f => ({...f, terms: e.target.checked}))} className="mt-0.5 accent-blue-500" />
              <span className="text-sm text-slate-400">I agree to the <a href="#" className="text-blue-400">Terms of Service</a> and <a href="#" className="text-blue-400">Privacy Policy</a></span>
            </label>
            <button type="submit" disabled={busy} className="btn-primary w-full flex items-center justify-center gap-2">
              {busy ? <><Spinner sm /> Creating…</> : '🚀 Create Account'}
            </button>
          </form>
          <p className="text-center text-sm text-slate-500 mt-5">
            Have an account? <Link to="/login" className="text-blue-400 hover:text-blue-300">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// PAGE: DASHBOARD
// ─────────────────────────────────────────────────────────────
const DashboardPage = () => {
  const { reading, history, alerts, sysStatus, clearAlerts } = useData();
  const [reportModal,  setReportModal]  = useState(false);
  const [reportData,   setReportData]   = useState(null);
  const [simBusy,      setSimBusy]      = useState(false);
  const [resetBusy,    setResetBusy]    = useState(false);

  const overall = reading?.overall_status || 'Safe';

  const paramCards = useMemo(() => {
    if (!reading?.parameters) return [];
    return Object.entries(PARAMS).map(([key, info]) => {
      const val   = reading.parameters[key];
      const st    = reading.status?.[key] || paramStatus(key, val);
      const spark = history.slice(-20).map(h => h[key]).filter(v => v != null);
      return { key, ...info, val, st, spark };
    });
  }, [reading, history]);

  const chartLine = useMemo(() => history.slice(-40).map(h => ({
    t: fmtTime(h.timestamp), pH: h.pH, Turbidity: h.turbidity, DO: h.dissolved_oxygen,
  })), [history]);

  const chartBar = useMemo(() => reading?.parameters ? [
    { n: 'pH',    v: reading.parameters.pH,                  ref: 8.5  },
    { n: 'Turb.', v: reading.parameters.turbidity,           ref: 5    },
    { n: 'DO',    v: reading.parameters.dissolved_oxygen,    ref: 14   },
    { n: 'Temp',  v: reading.parameters.temperature / 5,     ref: 7    },
  ] : [], [reading]);

  const statusGrad = {
    Safe:    'from-green-500/15 to-emerald-500/5 border-green-500/20',
    Caution: 'from-amber-500/15 to-yellow-500/5  border-amber-500/20',
    Unsafe:  'from-red-500/15   to-pink-500/5    border-red-500/20',
  };

  const simulate = async () => {
    setSimBusy(true);
    await fetch(`${API}/api/simulate_contamination`, { method: 'POST' });
    setSimBusy(false);
    toast.error('⚠️ Contamination event simulated!', { duration: 5000 });
  };

  const resetSys = async () => {
    setResetBusy(true);
    await fetch(`${API}/api/reset_system`, { method: 'POST' });
    setResetBusy(false);
    toast.success('✅ System reset to normal');
  };

  const genReport = async () => {
    const r = await fetch(`${API}/api/generate_report`);
    const d = await r.json();
    setReportData(d);
    setReportModal(true);
  };

  const activeAlerts = alerts.filter(a => !a.resolved).length;

  return (
    <div className="space-y-6">
      {/* Feature chips */}
      <div className="flex flex-wrap gap-2">
        {['🔴 Real-Time Monitoring','🤖 AI Anomaly Detection','📊 6 Parameters','🔔 Smart Alerts','📋 CPCB Compliance','👥 Citizen Portal'].map(f => (
          <span key={f} className="badge-info text-xs">{f}</span>
        ))}
      </div>

      {/* Status banner */}
      <div className={`card border bg-gradient-to-r ${statusGrad[overall] || statusGrad.Safe}`}>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <span className="text-5xl">{overall === 'Safe' ? '✅' : overall === 'Caution' ? '⚠️' : '🚨'}</span>
            <div>
              <h2 className="text-2xl font-black text-slate-100">Water Quality: {overall}</h2>
              <p className="text-slate-400 text-sm mt-0.5">
                {overall === 'Safe'    ? 'All parameters within CPCB BIS 10500:2012 limits' :
                 overall === 'Caution' ? 'Some parameters approaching threshold — monitor closely' :
                                        'Immediate action required! Multiple parameters critical'}
              </p>
            </div>
          </div>
          <StatusBadge status={overall.toLowerCase()} lg />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon="📊" label="Readings Today"   value={sysStatus.readings_count || 0} color="blue"   sub="Live sensor stream" />
        <StatCard icon="🔔" label="Active Alerts"    value={activeAlerts} color={activeAlerts > 0 ? 'red' : 'green'} pulse={activeAlerts > 0} sub={activeAlerts > 0 ? 'Needs attention' : 'All clear'} />
        <StatCard icon="📈" label="Compliance"        value={sysStatus.compliance_score || '98.5%'} color="green"  sub="CPCB BIS 10500:2012" />
        <StatCard icon="📡" label="Nodes Online"      value={`${sysStatus.hardware_nodes || 3}/3`}  color="purple" sub="Monitoring nodes" />
      </div>

      {/* Parameter cards */}
      <div>
        <h3 className="text-base font-bold text-slate-300 mb-4">📡 Live Parameter Readings</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {paramCards.map(p => (
            <div key={p.key} className={`card border hover:scale-[1.02] transition-transform ${
              p.st === 'safe' ? 'border-green-500/20' : p.st === 'warning' ? 'border-amber-500/20' : 'border-red-500/20'
            }`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{p.icon}</span>
                  <div>
                    <p className="text-[11px] text-slate-500 uppercase tracking-wider font-medium">{p.label}</p>
                    <div className="flex items-baseline gap-1 mt-0.5">
                      <span className="text-2xl font-black text-slate-100">{fmtVal(p.val)}</span>
                      <span className="text-sm text-slate-500">{p.unit}</span>
                    </div>
                  </div>
                </div>
                <StatusBadge status={p.st} />
              </div>
              <Sparkline data={p.spark} color={p.st === 'safe' ? '#22c55e' : p.st === 'warning' ? '#f59e0b' : '#ef4444'} />
              <p className="text-[11px] text-slate-600 mt-2">Safe range: {p.min}–{p.max} {p.unit}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 card">
          <h3 className="font-bold text-slate-200 mb-4">📈 Real-Time Trends</h3>
          <ResponsiveContainer width="100%" height={230}>
            <LineChart data={chartLine} margin={{ top:5, right:5, left:-25, bottom:0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff06" />
              <XAxis dataKey="t" stroke="#334155" tick={{ fontSize:10 }} interval="preserveStartEnd" />
              <YAxis stroke="#334155" tick={{ fontSize:10 }} />
              <Tooltip content={<ChartTip />} />
              <Legend wrapperStyle={{ fontSize:'11px' }} />
              <Line type="monotone" dataKey="pH"        stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="Turbidity" stroke="#8b5cf6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="DO"        stroke="#22c55e" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3 className="font-bold text-slate-200 mb-4">📊 Current Values</h3>
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={chartBar} margin={{ top:5, right:5, left:-25, bottom:0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff06" />
              <XAxis dataKey="n" stroke="#334155" tick={{ fontSize:10 }} />
              <YAxis stroke="#334155" tick={{ fontSize:10 }} />
              <Tooltip content={<ChartTip />} />
              <Bar dataKey="v" name="Value" radius={[4,4,0,0]}>
                {chartBar.map((_, i) => <Cell key={i} fill={['#3b82f6','#8b5cf6','#22c55e','#f59e0b'][i % 4]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Alerts + Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-200">🔔 Alert Feed</h3>
            <button onClick={clearAlerts} className="btn-secondary btn-sm text-xs">Clear All</button>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {alerts.length === 0 ? (
              <div className="text-center py-10">
                <div className="text-4xl mb-2">✅</div>
                <p className="text-slate-500 text-sm">No active alerts</p>
              </div>
            ) : alerts.map((a, i) => (
              <div key={i} className={`flex items-start gap-3 p-3 rounded-xl border ${
                a.severity === 'critical' ? 'bg-red-500/8 border-red-500/20' : 'bg-amber-500/8 border-amber-500/20'
              }`}>
                <span className="text-xl flex-shrink-0">{a.severity === 'critical' ? '🚨' : '⚠️'}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-200 truncate">{a.message}</p>
                  <p className="text-xs text-slate-600 mt-0.5">{fmtTime(a.timestamp)} · {fmtDate(a.timestamp)}</p>
                </div>
                <StatusBadge status={a.severity} />
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="font-bold text-slate-200 mb-4">🎛️ Control Panel</h3>
          <div className="space-y-3">
            <button onClick={genReport} className="btn-primary w-full flex items-center justify-center gap-2 text-sm">
              📄 Generate CPCB Report
            </button>
            <button onClick={simulate} disabled={simBusy}
              className="btn-secondary w-full flex items-center justify-center gap-2 text-sm border border-amber-500/30 text-amber-400 hover:bg-amber-500/10">
              {simBusy ? <Spinner sm /> : '⚠️'} Simulate Contamination
            </button>
            <button onClick={resetSys} disabled={resetBusy} className="btn-success w-full flex items-center justify-center gap-2 text-sm">
              {resetBusy ? <Spinner sm /> : '✅'} Reset System
            </button>
            <div className="pt-3 border-t border-white/5 space-y-1 text-xs text-slate-600">
              <p>📍 Nodes Online: {sysStatus.hardware_nodes || 3}</p>
              <p>🗄️ Data Points: {history.length}</p>
              <p>⏱️ Update: 1 s interval</p>
            </div>
          </div>
        </div>
      </div>

      {/* Report Modal */}
      <Modal open={reportModal} onClose={() => setReportModal(false)} title="📋 CPCB Compliance Report" lg>
        {reportData ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white/5 rounded-xl p-3">
                <p className="text-xs text-slate-500">Report ID</p>
                <p className="text-sm font-mono text-slate-200">{reportData.report_id}</p>
              </div>
              <div className="bg-white/5 rounded-xl p-3">
                <p className="text-xs text-slate-500">Compliance Score</p>
                <p className={`text-3xl font-black ${(reportData.compliance_score||0) >= 80 ? 'text-green-400' : 'text-red-400'}`}>
                  {reportData.compliance_score}%
                </p>
              </div>
            </div>
            <div className="tbl-wrap">
              <table className="tbl">
                <thead><tr><th>Parameter</th><th>Current</th><th>CPCB Range</th><th>Status</th></tr></thead>
                <tbody>
                  {Object.entries(reportData.parameters || {}).map(([k, v]) => (
                    <tr key={k}>
                      <td className="text-slate-300">{PARAMS[k]?.label || k}</td>
                      <td className="font-mono text-sm">{fmtVal(v.current)} {v.unit}</td>
                      <td className="text-slate-500 text-xs">{v.cpcb_min}–{v.cpcb_max}</td>
                      <td><StatusBadge status={v.is_compliant ? 'safe' : 'danger'} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button onClick={() => {
              const b = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
              const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = `${reportData.report_id}.json`; a.click();
              toast.success('Report downloaded!');
            }} className="btn-primary w-full">⬇️ Download Report (JSON)</button>
          </div>
        ) : <div className="flex justify-center py-10"><Spinner /></div>}
      </Modal>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// PAGE: MONITORING
// ─────────────────────────────────────────────────────────────
const MonitoringPage = () => {
  const { history } = useData();
  const [search,    setSearch]    = useState('');
  const [sortCol,   setSortCol]   = useState('timestamp');
  const [sortDir,   setSortDir]   = useState('desc');
  const [page,      setPage]      = useState(0);
  const [perPage,   setPerPage]   = useState(10);
  const [nodes,     setNodes]     = useState([]);
  const [addModal,  setAddModal]  = useState(false);
  const [newNode,   setNewNode]   = useState({ name:'', location:'', lat:'', lng:'', type:'Secondary' });

  useEffect(() => {
    fetch(`${API}/api/nodes`).then(r => r.json()).then(d => Array.isArray(d) && setNodes(d)).catch(() => {});
  }, []);

  const rows = useMemo(() => {
    let d = [...history];
    if (search) d = d.filter(r => (r.overall_status || '').toLowerCase().includes(search.toLowerCase()));
    d.sort((a, b) => {
      let [va, vb] = [a[sortCol], b[sortCol]];
      if (sortDir === 'desc') [va, vb] = [vb, va];
      return va < vb ? -1 : va > vb ? 1 : 0;
    });
    return d;
  }, [history, search, sortCol, sortDir]);

  const pages  = Math.max(1, Math.ceil(rows.length / perPage));
  const paged  = rows.slice(page * perPage, (page + 1) * perPage);

  const sort = col => { setSortCol(col); setSortDir(d => col === sortCol ? (d === 'asc' ? 'desc' : 'asc') : 'asc'); };
  const Arrow = ({ col }) => <span className="ml-0.5 text-slate-600">{sortCol === col ? (sortDir === 'asc' ? '↑' : '↓') : '↕'}</span>;

  const exportCsv = () => {
    const hdr = ['Timestamp','pH','TDS','Turbidity','Temperature','Conductivity','DO','Status'];
    const body = rows.map(r => [r.timestamp, r.pH, r.tds, r.turbidity, r.temperature, r.conductivity, r.dissolved_oxygen, r.overall_status]);
    const csv  = [hdr, ...body].map(r => r.join(',')).join('\n');
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], { type:'text/csv' })); a.download = 'aquapulse_data.csv'; a.click();
    toast.success('CSV downloaded!');
  };

  const addNode = async () => {
    const r = await fetch(`${API}/api/nodes`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(newNode) });
    const d = await r.json();
    setNodes(n => [...n, d]);
    setAddModal(false);
    setNewNode({ name:'', location:'', lat:'', lng:'', type:'Secondary' });
    toast.success('Node added!');
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon="📊" label="Total Readings"  value={history.length}                              color="blue" />
        <StatCard icon="🟢" label="Online Nodes"    value={nodes.filter(n=>n.status==='active').length} color="green" />
        <StatCard icon="🔧" label="Maintenance"     value={nodes.filter(n=>n.status==='maintenance').length} color="amber" />
        <StatCard icon="📅" label="Data Window"     value="Live"                                        color="purple" />
      </div>

      {/* Table */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="🔍 Filter by status…" className="input max-w-xs text-sm" />
          <select value={perPage} onChange={e => { setPerPage(Number(e.target.value)); setPage(0); }} className="select w-28 text-sm">
            {[10,25,50].map(n => <option key={n} value={n}>{n} / page</option>)}
          </select>
          <button onClick={exportCsv} className="btn-secondary btn-sm ml-auto text-xs flex items-center gap-1">
            📥 Export CSV
          </button>
        </div>

        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                {[['timestamp','Time'],['pH','pH'],['tds','TDS'],['turbidity','Turb.'],['temperature','Temp'],['conductivity','Cond.'],['dissolved_oxygen','DO'],['overall_status','Status']].map(([k,l]) => (
                  <th key={k} onClick={() => sort(k)} className="cursor-pointer hover:text-blue-400 select-none whitespace-nowrap">
                    {l}<Arrow col={k} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paged.length === 0
                ? <tr><td colSpan={8} className="text-center py-10 text-slate-600">No data yet. Readings appear here in real-time…</td></tr>
                : paged.map((r, i) => {
                  const c = r.overall_status === 'Safe' ? 'text-green-400' : r.overall_status === 'Caution' ? 'text-amber-400' : 'text-red-400';
                  return (
                    <tr key={i}>
                      <td className="text-slate-500 text-xs whitespace-nowrap">{fmtTime(r.timestamp)}</td>
                      {['pH','tds','turbidity','temperature','conductivity','dissolved_oxygen'].map(k => (
                        <td key={k} className="font-mono text-sm text-slate-300">{fmtVal(r[k])}</td>
                      ))}
                      <td><span className={`text-xs font-semibold ${c}`}>{r.overall_status || '—'}</span></td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between mt-4 text-xs text-slate-500">
          <span>{rows.length === 0 ? 'No records' : `${page * perPage + 1}–${Math.min((page+1)*perPage, rows.length)} of ${rows.length}`}</span>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage(p => Math.max(0, p-1))} disabled={page === 0} className="btn-secondary btn-sm disabled:opacity-30">← Prev</button>
            <span className="px-3 py-1.5 rounded-lg bg-white/5 text-slate-400">{page+1} / {pages}</span>
            <button onClick={() => setPage(p => Math.min(pages-1, p+1))} disabled={page >= pages-1} className="btn-secondary btn-sm disabled:opacity-30">Next →</button>
          </div>
        </div>
      </div>

      {/* Map + Nodes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="card">
          <h3 className="font-bold text-slate-200 mb-4">🗺️ Monitoring Node Map</h3>
          <div className="bg-slate-800/40 rounded-xl h-64 relative border border-white/5 overflow-hidden">
            <svg viewBox="0 0 400 240" className="w-full h-full">
              <defs>
                <linearGradient id="mapGrad" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="#0f172a" />
                  <stop offset="100%" stopColor="#1e293b" />
                </linearGradient>
              </defs>
              <rect fill="url(#mapGrad)" width="400" height="240" />
              {/* Stylised water/land shapes */}
              <ellipse cx="200" cy="120" rx="180" ry="90" fill="#1e293b" opacity="0.5" />
              <path d="M40,80 Q120,40 200,70 Q280,100 360,60" fill="none" stroke="#3b82f620" strokeWidth="25" strokeLinecap="round" />
              <path d="M40,160 Q130,140 200,155 Q270,170 360,145" fill="none" stroke="#06b6d420" strokeWidth="18" strokeLinecap="round" />
              {nodes.map((nd, i) => {
                const x = 80 + i * 120 + (i % 2) * 20;
                const y = 70 + (i % 2) * 55;
                const col = nd.status === 'active' ? '#22c55e' : nd.status === 'maintenance' ? '#f59e0b' : '#ef4444';
                return (
                  <g key={nd.id}>
                    <circle cx={x} cy={y} r="18" fill={col} opacity="0.15" />
                    <circle cx={x} cy={y} r="9"  fill={col} opacity="0.3" className="animate-pulse" />
                    <circle cx={x} cy={y} r="5"  fill={col} />
                    <text x={x} y={y + 24} textAnchor="middle" fill="#94a3b8" fontSize="9" fontFamily="Inter,sans-serif">{nd.name.split(' ')[0]}</text>
                  </g>
                );
              })}
              {/* Grid lines */}
              {[80,160,240,320].map(x => <line key={x} x1={x} y1="0" x2={x} y2="240" stroke="#ffffff04" strokeWidth="1" />)}
              {[60,120,180].map(y => <line key={y} x1="0" y1={y} x2="400" y2={y} stroke="#ffffff04" strokeWidth="1" />)}
            </svg>
            <div className="absolute bottom-3 left-3 flex gap-3 text-[10px] text-slate-400">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" />Active</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" />Maintenance</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />Offline</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-200">📡 Monitoring Nodes</h3>
            <button onClick={() => setAddModal(true)} className="btn-primary btn-sm text-xs">+ Add Node</button>
          </div>
          <div className="space-y-3">
            {nodes.map(nd => (
              <div key={nd.id} className="bg-white/5 rounded-xl p-3 border border-white/5">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-semibold text-slate-200 text-sm">{nd.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">📍 {nd.location}</p>
                    <p className="text-xs text-slate-600 mt-0.5">FW: {nd.firmware} · {nd.last_seen}</p>
                  </div>
                  <StatusBadge status={nd.status} />
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span>🔋</span>
                  <div className="flex-1 progress">
                    <div className={`progress-bar ${nd.battery > 60 ? 'bg-green-500' : nd.battery > 30 ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${nd.battery}%` }} />
                  </div>
                  <span>{nd.battery}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <Modal open={addModal} onClose={() => setAddModal(false)} title="➕ Add Monitoring Node">
        <div className="space-y-3">
          {[['name','Node Name'],['location','Location'],['lat','Latitude'],['lng','Longitude']].map(([k, l]) => (
            <div key={k}>
              <label className="block text-sm text-slate-400 mb-1">{l}</label>
              <input value={newNode[k]} onChange={e => setNewNode(n => ({...n,[k]:e.target.value}))} className="input" type={['lat','lng'].includes(k) ? 'number' : 'text'} />
            </div>
          ))}
          <div>
            <label className="block text-sm text-slate-400 mb-1">Type</label>
            <select value={newNode.type} onChange={e => setNewNode(n => ({...n,type:e.target.value}))} className="select">
              <option value="Primary">Primary</option>
              <option value="Secondary">Secondary</option>
            </select>
          </div>
          <button onClick={addNode} className="btn-primary w-full mt-2">Add Node</button>
        </div>
      </Modal>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// PAGE: AI ANALYTICS
// ─────────────────────────────────────────────────────────────
const AnalyticsPage = () => {
  const [data,     setData]     = useState(null);
  const [busy,     setBusy]     = useState(true);
  const [param,    setParam]    = useState('pH');
  const [tab,      setTab]      = useState('forecast');

  useEffect(() => {
    fetch(`${API}/api/analytics`).then(r => r.json()).then(d => { setData(d); setBusy(false); }).catch(() => setBusy(false));
  }, []);

  if (busy) return <div className="flex justify-center py-20"><Spinner /></div>;

  const forecast  = data?.forecasts?.[param]         || [];
  const metrics   = data?.metrics?.[param]            || {};
  const anomalies = data?.anomalies                   || [];
  const maint     = data?.maintenance                 || {};
  const trend     = data?.trend_data                  || [];
  const freq      = data?.anomaly_frequency           || [];

  const TABS = [
    { id:'forecast',    icon:'📈', label:'LSTM Forecast'       },
    { id:'anomaly',     icon:'🔍', label:'Anomaly Detection'   },
    { id:'maintenance', icon:'🔧', label:'Predictive Maint.'   },
    { id:'trend',       icon:'📅', label:'Trend Analysis'      },
  ];

  return (
    <div className="space-y-5">
      {/* AI badges */}
      <div className="flex flex-wrap gap-2">
        {[['🤖','LSTM Model'],['🔍','Isolation Forest'],['🧠','CNN-BiLSTM'],['⚙️','XGBoost'],['📊','SHAP Explainability']].map(([i, l]) => (
          <span key={l} className="badge-purple text-xs">{i} {l}</span>
        ))}
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon="🎯" label="Forecast Accuracy" value="94.2%"          color="green"  sub={`R² = ${metrics.r2 || '—'}`} />
        <StatCard icon="🔍" label="Anomalies (7d)"    value={anomalies.length} color="amber" sub="Detected events" />
        <StatCard icon="⚙️" label="Equipment Health"  value="74%"            color="blue"   sub="Avg across assets" />
        <StatCard icon="📈" label="Compliance Trend"  value="+2.1%"          color="purple" sub="vs last month" />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`tab ${tab === t.id ? 'tab-active' : ''}`}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* ── FORECAST ── */}
      {tab === 'forecast' && (
        <div className="space-y-5 animate-fade-in">
          <div className="card">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
              <h3 className="font-bold text-slate-200">📈 24-Hour LSTM Forecast</h3>
              <select value={param} onChange={e => setParam(e.target.value)} className="select w-44 text-sm">
                {Object.entries(PARAMS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
            </div>
            <ResponsiveContainer width="100%" height={260}>
              <ComposedChart data={forecast} margin={{ top:5, right:10, left:-20, bottom:0 }}>
                <defs>
                  <linearGradient id="confBand" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff06" />
                <XAxis dataKey="time" stroke="#334155" tick={{ fontSize:10 }} interval={3} />
                <YAxis stroke="#334155" tick={{ fontSize:10 }} />
                <Tooltip content={<ChartTip />} />
                <Legend wrapperStyle={{ fontSize:'11px' }} />
                <Area type="monotone" dataKey="upper" stroke="none" fill="url(#confBand)" name="Upper Conf." />
                <Area type="monotone" dataKey="lower" stroke="none" fill="#f8fafc"        fillOpacity={0}  name="Lower Conf." />
                <Line type="monotone" dataKey="predicted" stroke="#3b82f6" strokeWidth={2.5} dot={false} name={`${PARAMS[param]?.label} Forecast`} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="card">
              <h4 className="font-semibold text-slate-300 mb-4">📊 Model Accuracy Metrics</h4>
              {[['RMSE', metrics.rmse, 'Root Mean Square Error'],['MAE', metrics.mae, 'Mean Absolute Error'],['R²', metrics.r2, 'Coefficient of Determination']].map(([n,v,d]) => (
                <div key={n} className="flex items-center justify-between p-3 bg-white/5 rounded-xl mb-2">
                  <div>
                    <p className="text-sm font-semibold text-slate-200">{n}</p>
                    <p className="text-xs text-slate-500">{d}</p>
                  </div>
                  <span className="text-blue-400 font-bold text-lg">{v}</span>
                </div>
              ))}
            </div>
            <div className="card">
              <h4 className="font-semibold text-slate-300 mb-4">⏱️ Forecast Summary</h4>
              {[['1 Hour', 0], ['6 Hours', 5], ['24 Hours', 23]].map(([lbl, idx]) => {
                const pt = forecast[idx];
                return pt ? (
                  <div key={lbl} className="flex items-center justify-between p-3 bg-white/5 rounded-xl mb-2">
                    <div>
                      <p className="text-sm font-semibold text-slate-200">Next {lbl}</p>
                      <p className="text-xs text-slate-500">{pt.time}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-blue-400 font-bold">{pt.predicted} <span className="text-xs text-slate-500">{PARAMS[param]?.unit}</span></p>
                      <p className="text-xs text-slate-600">{pt.lower}–{pt.upper}</p>
                    </div>
                  </div>
                ) : null;
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── ANOMALY ── */}
      {tab === 'anomaly' && (
        <div className="space-y-5 animate-fade-in">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div className="card">
              <h3 className="font-bold text-slate-200 mb-4">🔍 Detected Anomalies</h3>
              <div className="space-y-3">
                {anomalies.map(a => (
                  <div key={a.id} className={`p-3 rounded-xl border flex items-start gap-3 ${
                    a.severity === 'critical' ? 'bg-red-500/8 border-red-500/20' : a.severity === 'high' ? 'bg-orange-500/8 border-orange-500/20' : 'bg-amber-500/8 border-amber-500/20'
                  }`}>
                    <span className="text-xl">{a.severity === 'critical' ? '🚨' : a.severity === 'high' ? '🔴' : '⚠️'}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <p className="text-sm font-semibold text-slate-200 capitalize">{a.parameter} Anomaly</p>
                        <StatusBadge status={a.severity} />
                        {a.resolved && <StatusBadge status="resolved" />}
                      </div>
                      <p className="text-xs text-slate-400">Value: <strong>{a.value}</strong> · Score: <strong>{(a.score*100).toFixed(0)}%</strong></p>
                      <p className="text-xs text-slate-600 mt-0.5">{fmtDate(a.timestamp)} {fmtTime(a.timestamp)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="card">
              <h3 className="font-bold text-slate-200 mb-4">📊 Frequency by Parameter</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={freq} layout="vertical" margin={{ top:5, right:15, left:50, bottom:0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff06" horizontal={false} />
                  <XAxis type="number" stroke="#334155" tick={{ fontSize:10 }} />
                  <YAxis type="category" dataKey="parameter" stroke="#334155" tick={{ fontSize:10 }} />
                  <Tooltip content={<ChartTip />} />
                  <Legend wrapperStyle={{ fontSize:'11px' }} />
                  <Bar dataKey="count"       name="Total"      fill="#f59e0b" radius={[0,4,4,0]} />
                  <Bar dataKey="last_7_days" name="Last 7 Days" fill="#ef4444" radius={[0,4,4,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* ── MAINTENANCE ── */}
      {tab === 'maintenance' && (
        <div className="space-y-5 animate-fade-in">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {Object.values(maint).map(eq => {
              const col = eq.health >= 80 ? '#22c55e' : eq.health >= 60 ? '#f59e0b' : '#ef4444';
              return (
                <div key={eq.name} className="card text-center">
                  <div className="text-4xl mb-3">{eq.icon}</div>
                  <h4 className="font-bold text-slate-200 mb-3">{eq.name}</h4>
                  <div className="flex justify-center mb-3"><Gauge value={eq.health} color={col} size={90} /></div>
                  <div className="mt-3 p-3 bg-white/5 rounded-xl text-left space-y-1">
                    <p className="text-xs text-slate-400">📅 Predicted failure: <strong className="text-slate-300">{eq.predicted_failure}</strong></p>
                    <p className="text-xs text-slate-500">{eq.recommendation}</p>
                  </div>
                  <div className="mt-2"><StatusBadge status={eq.priority} /></div>
                </div>
              );
            })}
          </div>
          <div className="card">
            <h3 className="font-bold text-slate-200 mb-4">📋 Maintenance Actions</h3>
            <div className="space-y-2">
              {Object.values(maint).map(eq => (
                <div key={eq.name} className={`flex items-center justify-between p-3 rounded-xl border ${
                  eq.priority === 'high' ? 'bg-red-500/8 border-red-500/20' : eq.priority === 'medium' ? 'bg-amber-500/8 border-amber-500/20' : 'bg-green-500/8 border-green-500/20'
                }`}>
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{eq.icon}</span>
                    <div>
                      <p className="text-sm font-semibold text-slate-200">{eq.name}</p>
                      <p className="text-xs text-slate-400">{eq.recommendation}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <StatusBadge status={eq.priority} />
                    <button onClick={() => toast.success(`Maintenance scheduled for ${eq.name}`)} className="btn-primary btn-sm text-xs">Schedule</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── TREND ── */}
      {tab === 'trend' && (
        <div className="space-y-5 animate-fade-in">
          <div className="card">
            <h3 className="font-bold text-slate-200 mb-4">📅 6-Month Parameter Trends</h3>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={trend} margin={{ top:5, right:10, left:-20, bottom:0 }}>
                <defs>
                  {[['#3b82f6','phGrad'],['#8b5cf6','turbGrad']].map(([col,id]) => (
                    <linearGradient key={id} id={id} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={col} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={col} stopOpacity={0} />
                    </linearGradient>
                  ))}
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff06" />
                <XAxis dataKey="month" stroke="#334155" tick={{ fontSize:10 }} />
                <YAxis stroke="#334155" tick={{ fontSize:10 }} />
                <Tooltip content={<ChartTip />} />
                <Legend wrapperStyle={{ fontSize:'11px' }} />
                <Area type="monotone" dataKey="pH"        stroke="#3b82f6" fill="url(#phGrad)"   strokeWidth={2} />
                <Area type="monotone" dataKey="turbidity" stroke="#8b5cf6" fill="url(#turbGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <h3 className="font-bold text-slate-200 mb-4">✅ Compliance Rate (6 Months)</h3>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={trend} margin={{ top:5, right:10, left:-20, bottom:0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff06" />
                <XAxis dataKey="month" stroke="#334155" tick={{ fontSize:10 }} />
                <YAxis domain={[85,100]} stroke="#334155" tick={{ fontSize:10 }} />
                <Tooltip content={<ChartTip />} />
                <ReferenceLine y={95} stroke="#22c55e30" strokeDasharray="4 4" />
                <Line type="monotone" dataKey="compliance" stroke="#22c55e" strokeWidth={2.5} dot={{ fill:'#22c55e', r:4 }} name="Compliance %" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <h3 className="font-bold text-slate-200 mb-4">📐 Statistical Summary</h3>
            <div className="tbl-wrap">
              <table className="tbl">
                <thead><tr><th>Parameter</th><th>Min (Safe)</th><th>Max (Safe)</th><th>Midpoint</th><th>Trend</th></tr></thead>
                <tbody>
                  {Object.entries(PARAMS).map(([k, v]) => (
                    <tr key={k}>
                      <td><div className="flex items-center gap-1.5"><span>{v.icon}</span><span className="text-slate-300">{v.label}</span></div></td>
                      <td className="font-mono text-slate-400">{v.min} {v.unit}</td>
                      <td className="font-mono text-slate-400">{v.max} {v.unit}</td>
                      <td className="font-mono text-slate-300">{((v.min+v.max)/2).toFixed(1)} {v.unit}</td>
                      <td><span className="text-green-400 text-xs">↗ Stable</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// PAGE: COMPLIANCE
// ─────────────────────────────────────────────────────────────
const CompliancePage = () => {
  const { alerts } = useData();
  const [form,    setForm]    = useState({ start:'', end:'', type:'daily' });
  const [report,  setReport]  = useState(null);
  const [busy,    setBusy]    = useState(false);
  const [preview, setPreview] = useState(false);
  const [sevFilt, setSevFilt] = useState('all');

  const gen = async () => {
    setBusy(true);
    const r = await fetch(`${API}/api/generate_report`);
    const d = await r.json();
    setReport(d); setBusy(false); setPreview(true);
    toast.success('Report generated!');
  };

  const compData = report
    ? Object.entries(report.parameters || {}).map(([k,v]) => ({ name: PARAMS[k]?.label||k, score: v.is_compliant ? 100 : 0, fill: v.is_compliant ? '#22c55e' : '#ef4444' }))
    : Object.entries(PARAMS).map(([k,v]) => ({ name: v.label, score: 92 + Math.random()*8, fill: '#22c55e' }));

  const filtAlerts = sevFilt === 'all' ? alerts : alerts.filter(a => a.severity === sevFilt);

  const mockReports = [
    { id:'AQP-20260817-0052', date:'2026-08-17', type:'Daily',   score:98.2 },
    { id:'AQP-20260811-0031', date:'2026-08-11', type:'Weekly',  score:96.7 },
    { id:'AQP-20260801-0010', date:'2026-08-01', type:'Monthly', score:94.1 },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon="📋" label="Compliance Score"    value="98.5%"           color="green"  sub="CPCB BIS 10500:2012" />
        <StatCard icon="✅" label="Compliant Parameters" value="6 / 6"           color="green"  sub="All parameters" />
        <StatCard icon="🚨" label="Violations (30d)"    value="2"               color="red"    sub="Minor violations" />
        <StatCard icon="📄" label="Reports Generated"   value={mockReports.length} color="blue" sub="This month" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Generator form */}
        <div className="card">
          <h3 className="font-bold text-slate-200 mb-5">📄 Report Generator</h3>
          <div className="space-y-4">
            <div>
              <label className="text-xs text-slate-500 block mb-1.5">Report Type</label>
              <select value={form.type} onChange={e => setForm(f => ({...f, type:e.target.value}))} className="select text-sm">
                {[['daily','Daily Report'],['weekly','Weekly Report'],['monthly','Monthly Report'],['compliance','Full Compliance']].map(([v,l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 block mb-1.5">Start Date</label>
              <input type="date" value={form.start} onChange={e => setForm(f => ({...f,start:e.target.value}))} className="input text-sm" />
            </div>
            <div>
              <label className="text-xs text-slate-500 block mb-1.5">End Date</label>
              <input type="date" value={form.end} onChange={e => setForm(f => ({...f,end:e.target.value}))} className="input text-sm" />
            </div>
            <button onClick={gen} disabled={busy} className="btn-primary w-full flex items-center justify-center gap-2 text-sm">
              {busy ? <Spinner sm /> : '📋'} Generate Report
            </button>
            <div className="pt-3 border-t border-white/5">
              <p className="text-xs text-slate-500 mb-2 font-medium">BIS 10500:2012 Standards</p>
              {Object.entries(PARAMS).map(([k, v]) => (
                <div key={k} className="flex justify-between text-xs py-1 border-b border-white/5">
                  <span className="text-slate-400">{v.icon} {v.label}</span>
                  <span className="font-mono text-slate-500">{v.min}–{v.max} {v.unit}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-5">
          <div className="card">
            <h3 className="font-bold text-slate-200 mb-4">📊 Parameter Compliance</h3>
            <ResponsiveContainer width="100%" height={190}>
              <BarChart data={compData} margin={{ top:5, right:5, left:-25, bottom:0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff06" />
                <XAxis dataKey="name" stroke="#334155" tick={{ fontSize:9 }} />
                <YAxis domain={[0,100]} stroke="#334155" tick={{ fontSize:10 }} />
                <Tooltip content={<ChartTip />} />
                <ReferenceLine y={80} stroke="#f59e0b30" strokeDasharray="4 4" />
                <Bar dataKey="score" name="Compliance %" radius={[4,4,0,0]}>
                  {compData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-slate-200">📁 Generated Reports</h3>
              <div className="flex gap-1">
                <span className="badge-info text-[10px]">Auto: Daily 6PM</span>
                <span className="badge-purple text-[10px]">Weekly Monday</span>
              </div>
            </div>
            <div className="tbl-wrap">
              <table className="tbl">
                <thead><tr><th>Report ID</th><th>Date</th><th>Type</th><th>Score</th><th>Action</th></tr></thead>
                <tbody>
                  {mockReports.map(r => (
                    <tr key={r.id}>
                      <td className="font-mono text-[11px] text-slate-500">{r.id}</td>
                      <td className="text-sm text-slate-300">{r.date}</td>
                      <td><span className="badge-info text-xs">{r.type}</span></td>
                      <td>
                        <div className="flex items-center gap-2">
                          <span className="text-green-400 font-bold text-sm">{r.score}%</span>
                          <div className="w-14 progress"><div className="progress-bar bg-green-500" style={{ width:`${r.score}%` }} /></div>
                        </div>
                      </td>
                      <td><button onClick={() => toast.success('Downloading…')} className="btn-secondary btn-sm text-xs">⬇️ Download</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Alert history */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <h3 className="font-bold text-slate-200">🔔 Alert History</h3>
          <div className="flex gap-1.5 ml-auto">
            {['all','critical','warning'].map(f => (
              <button key={f} onClick={() => setSevFilt(f)}
                className={`btn-sm text-xs ${sevFilt === f ? 'btn-primary' : 'btn-secondary'}`}>
                {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>
        <div className="space-y-2 max-h-72 overflow-y-auto">
          {filtAlerts.length === 0
            ? <p className="text-center text-slate-600 py-8">No alerts in this category</p>
            : filtAlerts.map((a, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-white/3 border border-white/5 hover:bg-white/5 transition-all">
                <span className="text-xl flex-shrink-0">{a.severity === 'critical' ? '🚨' : '⚠️'}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-300 truncate">{a.message}</p>
                  <p className="text-xs text-slate-600">{fmtDate(a.timestamp)} · {fmtTime(a.timestamp)}</p>
                </div>
                <StatusBadge status={a.severity} />
                <button onClick={() => toast.success('Alert marked resolved')} className="btn-success btn-sm text-xs flex-shrink-0">✓ Resolve</button>
              </div>
            ))}
        </div>
      </div>

      {/* Preview modal */}
      <Modal open={preview} onClose={() => setPreview(false)} title="📋 CPCB Report Preview" lg>
        {report && (
          <div className="space-y-4">
            <div className="flex items-start justify-between bg-gradient-to-r from-blue-500/10 to-cyan-500/5 border border-blue-500/20 rounded-xl p-4">
              <div>
                <h4 className="text-blue-400 font-bold text-lg">AquaPulse CPCB Report</h4>
                <p className="text-xs text-slate-400 mt-1">ID: {report.report_id}</p>
                <p className="text-xs text-slate-500">Generated: {fmtDate(report.timestamp)}</p>
              </div>
              <div className="text-right">
                <p className="text-slate-500 text-xs">Score</p>
                <p className={`text-3xl font-black ${(report.compliance_score||0) >= 80 ? 'text-green-400' : 'text-red-400'}`}>{report.compliance_score}%</p>
              </div>
            </div>
            <div className="tbl-wrap">
              <table className="tbl">
                <thead><tr><th>Parameter</th><th>Current</th><th>Avg</th><th>CPCB Range</th><th>Status</th></tr></thead>
                <tbody>
                  {Object.entries(report.parameters || {}).map(([k,v]) => (
                    <tr key={k}>
                      <td className="text-slate-300">{PARAMS[k]?.label||k}</td>
                      <td className="font-mono text-sm">{fmtVal(v.current)} {v.unit}</td>
                      <td className="font-mono text-sm text-slate-500">{fmtVal(v.avg)}</td>
                      <td className="text-xs text-slate-500">{v.cpcb_min}–{v.cpcb_max}</td>
                      <td>{v.is_compliant ? '✅' : '❌'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex gap-3">
              <button onClick={() => {
                const b = new Blob([JSON.stringify(report,null,2)],{type:'application/json'});
                const a = document.createElement('a'); a.href=URL.createObjectURL(b); a.download=`${report.report_id}.json`; a.click();
                toast.success('Downloaded!');
              }} className="btn-primary flex-1 text-sm">⬇️ Download JSON</button>
              <button onClick={() => setPreview(false)} className="btn-secondary flex-1 text-sm">Close</button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// PAGE: CITIZEN PORTAL
// ─────────────────────────────────────────────────────────────
const CitizenPage = () => {
  const { reading } = useData();
  const [issues,   setIssues]   = useState([]);
  const [form,     setForm]     = useState({ location:'', type:'Color', description:'' });
  const [busy,     setBusy]     = useState(false);
  const [faqIdx,   setFaqIdx]   = useState(null);
  const [notifs,   setNotifs]   = useState({ sms:true, email:true, push:false });

  useEffect(() => {
    fetch(`${API}/api/citizen/issues`).then(r => r.json()).then(d => Array.isArray(d) && setIssues(d)).catch(() => {});
  }, []);

  const submit = async e => {
    e.preventDefault();
    if (!form.location || !form.description) return toast.error('Please fill all required fields');
    setBusy(true);
    const r = await fetch(`${API}/api/citizen/issues`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(form) });
    const d = await r.json();
    setIssues(p => [...p, d]);
    setForm({ location:'', type:'Color', description:'' });
    setBusy(false);
    toast.success('Issue submitted! 📋 Track below.');
  };

  const params  = reading?.parameters;
  const overall = reading?.overall_status || 'Safe';

  const faqs = [
    { q:'What is TDS and why does it matter?',           a:'Total Dissolved Solids measures the concentration of dissolved substances. Values above 500 ppm indicate potential health risks and the water should be treated before drinking.' },
    { q:'What pH range is safe for drinking water?',     a:'The CPCB BIS 10500:2012 standard specifies pH 6.5–8.5. Values outside this range can cause corrosion or mineral buildup in plumbing.' },
    { q:'How often is water quality measured?',          a:'Sensors measure every second. Data is logged every 3 hours for official records. You can see live readings on our monitoring dashboard.' },
    { q:'What should I do if water looks unusual?',      a:'Stop using it for drinking and cooking. Report the issue via this portal. Use bottled water until the issue is resolved.' },
    { q:'How do I get alerts for unsafe water quality?', a:'Enable SMS or email alerts in the Notifications panel below. You\'ll receive instant notifications when quality drops below safe thresholds in your ward.' },
  ];

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className={`card border ${overall === 'Safe' ? 'from-green-500/15 to-emerald-500/5 border-green-500/20' : 'from-red-500/15 to-pink-500/5 border-red-500/20'} bg-gradient-to-r`}>
        <div className="flex items-center gap-4">
          <span className="text-5xl">{overall === 'Safe' ? '✅' : '🚨'}</span>
          <div>
            <h2 className="text-xl font-black text-slate-100">Water Quality: <span className={overall === 'Safe' ? 'text-green-400' : 'text-red-400'}>{overall}</span></h2>
            <p className="text-slate-400 text-sm mt-0.5">
              {overall === 'Safe' ? 'Your tap water is safe to drink. All CPCB parameters are within limits.' : 'Water quality issues detected. Please use boiled or bottled water.'}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Readings */}
        <div className="card">
          <h3 className="font-bold text-slate-200 mb-4">💧 Current Readings</h3>
          <div className="space-y-3">
            {params && [
              { label:'pH Level',   val: params.pH,               unit:'',    safe:'6.5–8.5',  icon:'🧪' },
              { label:'TDS',        val: params.tds,              unit:'ppm', safe:'< 500 ppm', icon:'💧' },
              { label:'Turbidity',  val: params.turbidity,        unit:'NTU', safe:'< 5 NTU',   icon:'🌫️' },
            ].map(p => (
              <div key={p.label} className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{p.icon}</span>
                  <div>
                    <p className="text-sm font-medium text-slate-200">{p.label}</p>
                    <p className="text-xs text-slate-600">Safe: {p.safe}</p>
                  </div>
                </div>
                <p className="font-bold text-slate-100">{fmtVal(p.val)} <span className="text-xs text-slate-500">{p.unit}</span></p>
              </div>
            ))}
            {!params && <p className="text-slate-600 text-sm text-center py-6">Connecting to sensors…</p>}
          </div>
        </div>

        {/* Ward Map */}
        <div className="card">
          <h3 className="font-bold text-slate-200 mb-4">🗺️ Ward Quality Map</h3>
          <div className="bg-slate-800/40 rounded-xl h-48 relative border border-white/5 overflow-hidden">
            <svg viewBox="0 0 300 180" className="w-full h-full">
              <rect fill="#1e293b" width="300" height="180" />
              {[
                { x:55,  y:60,  r:32, col:'#22c55e', lbl:'Ward 5'  },
                { x:150, y:75,  r:38, col:'#22c55e', lbl:'Ward 12' },
                { x:240, y:65,  r:28, col:'#f59e0b', lbl:'Ward 18' },
                { x:100, y:128, r:24, col:'#22c55e', lbl:'Ward 3'  },
                { x:205, y:140, r:26, col:'#22c55e', lbl:'Ward 9'  },
              ].map((z, i) => (
                <g key={i}>
                  <circle cx={z.x} cy={z.y} r={z.r} fill={z.col} opacity="0.18" />
                  <circle cx={z.x} cy={z.y} r={5}   fill={z.col} />
                  <text x={z.x} y={z.y + z.r + 12} textAnchor="middle" fill="#94a3b8" fontSize="8" fontFamily="Inter,sans-serif">{z.lbl}</text>
                </g>
              ))}
            </svg>
            <div className="absolute bottom-2 left-2 flex gap-2 text-[10px] text-slate-400">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" />Safe</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" />Caution</span>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="card">
          <h3 className="font-bold text-slate-200 mb-4">🔔 Alert Preferences</h3>
          <div className="space-y-3">
            {[['sms','📱 SMS Alerts','Instant text for unsafe water'],['email','📧 Email Alerts','Detailed reports via email'],['push','🔔 Push Notifications','Browser push alerts']].map(([k,lbl,desc]) => (
              <div key={k} className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                <div>
                  <p className="text-sm font-medium text-slate-200">{lbl}</p>
                  <p className="text-xs text-slate-500">{desc}</p>
                </div>
                <button onClick={() => setNotifs(n => ({...n,[k]:!n[k]}))}
                  className={`toggle ${notifs[k] ? 'toggle-on' : 'toggle-off'}`}>
                  <span className={`toggle-knob ${notifs[k] ? 'right-0.5' : 'left-0.5'}`} />
                </button>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
            <p className="text-xs text-blue-400">📍 Tracking: Ahmedabad Ward 5, 12</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Issue form */}
        <div className="card">
          <h3 className="font-bold text-slate-200 mb-1">📝 Report a Water Issue</h3>
          <p className="text-slate-500 text-xs mb-4">Submit a complaint about your tap water</p>
          <form onSubmit={submit} className="space-y-3">
            <div>
              <label className="text-xs text-slate-500 block mb-1">Location / Address *</label>
              <input type="text" value={form.location} onChange={e => setForm(f => ({...f,location:e.target.value}))}
                className="input text-sm" placeholder="e.g. 123 Main St, Ward 5, Ahmedabad" required />
            </div>
            <div>
              <label className="text-xs text-slate-500 block mb-1">Issue Type *</label>
              <select value={form.type} onChange={e => setForm(f => ({...f,type:e.target.value}))} className="select text-sm">
                {['Color','Odor','Taste','Health Concern','Low Pressure','Contamination','Other'].map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 block mb-1">Description *</label>
              <textarea value={form.description} onChange={e => setForm(f => ({...f,description:e.target.value}))}
                className="input h-24 resize-none text-sm" placeholder="Describe the issue in detail…" required />
            </div>
            <div className="border-2 border-dashed border-white/10 rounded-xl p-4 text-center cursor-pointer hover:border-blue-500/30 transition">
              <p className="text-slate-500 text-sm">📷 Upload Photo (optional)</p>
              <p className="text-xs text-slate-600 mt-0.5">Click to browse or drag & drop</p>
            </div>
            <button type="submit" disabled={busy} className="btn-primary w-full flex items-center justify-center gap-2 text-sm">
              {busy ? <Spinner sm /> : '📤'} Submit Report
            </button>
          </form>
        </div>

        {/* Complaints tracker */}
        <div className="card">
          <h3 className="font-bold text-slate-200 mb-1">📋 My Complaints</h3>
          <p className="text-slate-500 text-xs mb-4">Track your submitted issues</p>
          <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
            {issues.length === 0
              ? <div className="text-center py-10"><div className="text-4xl mb-2">📭</div><p className="text-slate-600 text-sm">No issues submitted yet</p></div>
              : issues.map(iss => (
                <div key={iss.id} className="p-3 bg-white/5 rounded-xl border border-white/5">
                  <div className="flex items-start justify-between mb-1">
                    <p className="text-sm font-medium text-slate-200">{iss.type} Issue</p>
                    <StatusBadge status={iss.status} />
                  </div>
                  <p className="text-xs text-slate-500">📍 {iss.location}</p>
                  {iss.description && <p className="text-xs text-slate-600 mt-1">{iss.description.substring(0,70)}{iss.description.length>70?'…':''}</p>}
                  <p className="text-xs text-slate-700 mt-1">Submitted: {iss.submitted}</p>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Educational Resources */}
      <div className="card">
        <h3 className="font-bold text-slate-200 mb-5">📚 Educational Resources</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[['💧','Water Quality Basics','Understanding pH, TDS & turbidity'],['🛡️','Safety Guidelines','CPCB standards for drinking water'],['🚰','Water Treatment','How municipalities treat water'],['🌿','Conservation Tips','Reduce, reuse & protect water']].map(([ic,t,d]) => (
            <div key={t} onClick={() => toast(`📖 Opening: ${t}`, { icon:'📚' })}
              className="p-4 bg-white/5 rounded-xl border border-white/5 hover:border-blue-500/20 hover:bg-white/8 transition cursor-pointer">
              <div className="text-3xl mb-2">{ic}</div>
              <h4 className="font-semibold text-slate-200 text-sm mb-1">{t}</h4>
              <p className="text-xs text-slate-500">{d}</p>
            </div>
          ))}
        </div>
        <div>
          <h4 className="font-semibold text-slate-300 mb-3">❓ Frequently Asked Questions</h4>
          <div className="space-y-2">
            {faqs.map((faq, i) => (
              <div key={i} className="border border-white/5 rounded-xl overflow-hidden">
                <button onClick={() => setFaqIdx(faqIdx === i ? null : i)}
                  className="w-full flex items-center justify-between p-3.5 text-left hover:bg-white/5 transition">
                  <span className="text-sm font-medium text-slate-300 pr-4">{faq.q}</span>
                  <span className={`text-slate-500 transition-transform flex-shrink-0 ${faqIdx === i ? 'rotate-180' : ''}`}>▼</span>
                </button>
                {faqIdx === i && (
                  <div className="px-4 pb-4 text-sm text-slate-400 border-t border-white/5 pt-3 animate-fade-in leading-relaxed">
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// PAGE: SETTINGS
// ─────────────────────────────────────────────────────────────
const SettingsPage = () => {
  const { dark, toggle: toggleTheme } = useTheme();
  const [tab,       setTab]       = useState('system');
  const [settings,  setSettings]  = useState(null);
  const [users,     setUsers]     = useState([]);
  const [nodes,     setNodes]     = useState([]);
  const [addUModal, setAddUModal] = useState(false);
  const [newUser,   setNewUser]   = useState({ email:'', full_name:'', role:'citizen', organization:'' });
  const [clrModal,  setClrModal]  = useState(false);
  const [saved,     setSaved]     = useState(false);

  useEffect(() => {
    fetch(`${API}/api/settings`).then(r => r.json()).then(setSettings).catch(() => {});
    fetch(`${API}/api/users`).then(r => r.json()).then(d => Array.isArray(d) && setUsers(d)).catch(() => {});
    fetch(`${API}/api/nodes`).then(r => r.json()).then(d => Array.isArray(d) && setNodes(d)).catch(() => {});
  }, []);

  const saveSettings = async () => {
    if (!settings) return;
    await fetch(`${API}/api/settings`, { method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(settings) });
    setSaved(true); toast.success('Settings saved!');
    setTimeout(() => setSaved(false), 2500);
  };

  const addUser = async () => {
    const r = await fetch(`${API}/api/users`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(newUser) });
    const d = await r.json();
    setUsers(u => [...u, d]); setAddUModal(false);
    setNewUser({ email:'', full_name:'', role:'citizen', organization:'' });
    toast.success('User added!');
  };

  const delUser = async id => {
    await fetch(`${API}/api/users/${id}`, { method:'DELETE' });
    setUsers(u => u.filter(x => x.id !== id));
    toast.success('User removed');
  };

  const TABS = [
    { id:'system', icon:'⚙️', label:'System'  },
    { id:'users',  icon:'👥', label:'Users'   },
    { id:'nodes',  icon:'📡', label:'Nodes'   },
    { id:'data',   icon:'🗄️', label:'Data'    },
  ];

  const Toggle = ({ on, onToggle }) => (
    <button onClick={onToggle} className={`toggle ${on ? 'toggle-on' : 'toggle-off'} relative`}>
      <span className={`toggle-knob absolute top-0.5 ${on ? 'right-0.5' : 'left-0.5'}`} />
    </button>
  );

  return (
    <div className="space-y-5">
      <div className="flex gap-2 flex-wrap">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`tab ${tab === t.id ? 'tab-active' : ''}`}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* ── SYSTEM ── */}
      {tab === 'system' && settings && (
        <div className="space-y-5 animate-fade-in">
          <div className="card">
            <h3 className="font-bold text-slate-200 mb-5">🎛️ Alert Thresholds</h3>
            <div className="space-y-5">
              {Object.entries(settings.thresholds || {}).map(([k, r]) => {
                const info = PARAMS[k];
                return (
                  <div key={k}>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-slate-300">{info?.icon} {info?.label || k}</label>
                      <span className="text-xs text-blue-400 font-mono">{r.min} – {r.max} {info?.unit}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-600 w-8 text-right">{r.min}</span>
                      <input type="range" min="0" max={info?.max * 1.5 || 1000} value={r.max}
                        onChange={e => setSettings(s => ({ ...s, thresholds: { ...s.thresholds, [k]: { ...r, max: Number(e.target.value) } } }))}
                        className="flex-1 accent-blue-500 cursor-pointer" />
                      <span className="text-xs text-slate-500 w-12">{r.max}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="card">
              <h3 className="font-bold text-slate-200 mb-4">⏱️ Sampling & Reports</h3>
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-slate-500 block mb-1.5">Sampling Frequency</label>
                  <select value={settings.sampling_interval} onChange={e => setSettings(s => ({...s, sampling_interval: Number(e.target.value)}))} className="select text-sm">
                    {[1,3,6,12,24].map(h => <option key={h} value={h}>{h} hour{h!==1?'s':''}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1.5">Data Retention</label>
                  <select value={settings.data_retention_days} onChange={e => setSettings(s => ({...s, data_retention_days: Number(e.target.value)}))} className="select text-sm">
                    {[30,90,180,365,730].map(d => <option key={d} value={d}>{d} days</option>)}
                  </select>
                </div>
                <div className="pt-2 border-t border-white/5 space-y-2">
                  {[['auto_report_daily','📅 Daily Report (6 PM)'],['auto_report_weekly','📅 Weekly (Monday)'],['auto_report_monthly','📅 Monthly (1st)']].map(([k,l]) => (
                    <label key={k} className="flex items-center gap-2 cursor-pointer">
                      <input type="checkbox" checked={settings[k]||false} onChange={e => setSettings(s => ({...s,[k]:e.target.checked}))} className="accent-blue-500" />
                      <span className="text-sm text-slate-400">{l}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="font-bold text-slate-200 mb-4">🔔 Notifications & Theme</h3>
              <div className="space-y-3">
                {[['email','📧 Email Alerts'],['sms','📱 SMS Alerts'],['push','🔔 Push Notifications']].map(([k,l]) => (
                  <div key={k} className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                    <span className="text-sm text-slate-300">{l}</span>
                    <Toggle on={settings.notifications?.[k]} onToggle={() => setSettings(s => ({...s, notifications:{...s.notifications,[k]:!s.notifications?.[k]}}))} />
                  </div>
                ))}
                <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border-t border-white/5 mt-1">
                  <span className="text-sm text-slate-300">🌙 Dark Mode</span>
                  <Toggle on={dark} onToggle={toggleTheme} />
                </div>
              </div>
            </div>
          </div>

          <button onClick={saveSettings} className={`btn-primary px-8 flex items-center gap-2 ${saved ? '!from-green-500 !to-emerald-500' : ''}`}>
            {saved ? '✅ Saved!' : '💾 Save Settings'}
          </button>
        </div>
      )}

      {/* ── USERS ── */}
      {tab === 'users' && (
        <div className="card animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-200">👥 User Management</h3>
            <button onClick={() => setAddUModal(true)} className="btn-primary btn-sm text-xs">+ Add User</button>
          </div>
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Organization</th><th>Status</th><th></th></tr></thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id}>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                          {u.full_name?.charAt(0)}
                        </div>
                        <span className="text-sm text-slate-300">{u.full_name}</span>
                      </div>
                    </td>
                    <td className="text-slate-500 text-xs">{u.email}</td>
                    <td><span className={`badge text-xs ${u.role==='admin'?'badge-danger':u.role==='government'?'badge-info':'badge-success'} capitalize`}>{u.role}</span></td>
                    <td className="text-slate-500 text-xs">{u.organization||'—'}</td>
                    <td><StatusBadge status={u.status||'active'} /></td>
                    <td><button onClick={() => delUser(u.id)} className="btn-danger btn-sm text-xs">🗑️</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── NODES ── */}
      {tab === 'nodes' && (
        <div className="space-y-4 animate-fade-in">
          {nodes.map(nd => (
            <div key={nd.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-slate-200">{nd.name}</h4>
                    <StatusBadge status={nd.status} />
                    <span className="badge-purple text-xs">{nd.type}</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-slate-500">
                    <span>📍 {nd.location}</span>
                    <span>🔋 {nd.battery}%</span>
                    <span>💾 FW {nd.firmware}</span>
                    <span>🕐 {nd.last_seen}</span>
                  </div>
                </div>
              </div>
              <div className="progress mb-3">
                <div className={`progress-bar ${nd.battery>60?'bg-green-500':nd.battery>30?'bg-amber-500':'bg-red-500'}`} style={{ width:`${nd.battery}%` }} />
              </div>
              <div className="flex gap-2">
                <button onClick={() => toast.success(`Calibrating ${nd.name}…`)} className="btn-primary btn-sm text-xs">🔧 Calibrate</button>
                <button onClick={() => toast(`Editing ${nd.name}`, { icon:'✏️' })} className="btn-secondary btn-sm text-xs">✏️ Edit</button>
                <button onClick={() => toast.success('Firmware update queued')} className="btn-secondary btn-sm text-xs">⬆️ FW Update</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── DATA ── */}
      {tab === 'data' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 animate-fade-in">
          <div className="card">
            <h3 className="font-bold text-slate-200 mb-4">🗄️ Data Management</h3>
            <div className="space-y-3">
              {[
                ['⬇️ Export as CSV',   'Complete dataset as CSV file',    () => toast.success('CSV export started!')],
                ['⬇️ Export as JSON',  'Full dataset with metadata',       () => toast.success('JSON export ready!')],
                ['💾 Create Backup',   'Full system backup to archive',    () => toast.success('Backup created!')],
              ].map(([lbl, desc, fn]) => (
                <div key={lbl} className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                  <div>
                    <p className="text-sm font-medium text-slate-200">{lbl.split(' ').slice(1).join(' ')}</p>
                    <p className="text-xs text-slate-500">{desc}</p>
                  </div>
                  <button onClick={fn} className="btn-primary btn-sm text-xs">{lbl.split(' ')[0]}</button>
                </div>
              ))}
              <div className="flex items-center justify-between p-3 bg-red-500/8 border border-red-500/20 rounded-xl">
                <div>
                  <p className="text-sm font-medium text-red-400">Clear Historical Data</p>
                  <p className="text-xs text-red-500/60">This action cannot be undone</p>
                </div>
                <button onClick={() => setClrModal(true)} className="btn-danger btn-sm text-xs">🗑️ Clear</button>
              </div>
            </div>
          </div>
          <div className="card">
            <h3 className="font-bold text-slate-200 mb-4">📊 Storage Stats</h3>
            <div className="space-y-3">
              {[['Readings Stored','2.4k records',78],['Alert History','127 alerts',23],['Report Archive','42 reports',15],['Media Files','18 photos',5]].map(([l,c,p]) => (
                <div key={l} className="p-3 bg-white/5 rounded-xl">
                  <div className="flex justify-between text-sm mb-1.5">
                    <span className="text-slate-300">{l}</span>
                    <span className="text-slate-500 text-xs">{c}</span>
                  </div>
                  <div className="progress"><div className="progress-bar bg-blue-500" style={{ width:`${p}%` }} /></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Add User Modal */}
      <Modal open={addUModal} onClose={() => setAddUModal(false)} title="➕ Add New User">
        <div className="space-y-3">
          {[['full_name','Full Name','text'],['email','Email Address','email'],['organization','Organization','text']].map(([k,l,t]) => (
            <div key={k}>
              <label className="block text-sm text-slate-400 mb-1">{l}</label>
              <input type={t} value={newUser[k]} onChange={e => setNewUser(u => ({...u,[k]:e.target.value}))} className="input text-sm" />
            </div>
          ))}
          <div>
            <label className="block text-sm text-slate-400 mb-1">Role</label>
            <select value={newUser.role} onChange={e => setNewUser(u => ({...u, role:e.target.value}))} className="select text-sm">
              <option value="citizen">Citizen</option>
              <option value="government">Government Official</option>
              <option value="admin">Administrator</option>
            </select>
          </div>
          <button onClick={addUser} className="btn-primary w-full mt-2 text-sm">Add User</button>
        </div>
      </Modal>

      {/* Confirm Clear Modal */}
      <Modal open={clrModal} onClose={() => setClrModal(false)} title="⚠️ Confirm Data Clear">
        <div className="text-center py-4">
          <div className="text-5xl mb-4">🗑️</div>
          <p className="text-slate-300 mb-2">This will permanently delete all historical data.</p>
          <p className="text-red-400 text-sm mb-6">This action cannot be undone!</p>
          <div className="flex gap-3">
            <button onClick={() => { setClrModal(false); fetch(`${API}/api/reset_system`,{method:'POST'}); toast.success('Data cleared'); }} className="btn-danger flex-1">Yes, Clear All</button>
            <button onClick={() => setClrModal(false)} className="btn-secondary flex-1">Cancel</button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────
// PAGE TITLES MAP
// ─────────────────────────────────────────────────────────────
const TITLES = {
  '/':            'Dashboard',
  '/monitoring':  'Real-Time Monitoring',
  '/analytics':   'AI Analytics',
  '/compliance':  'Compliance & Reports',
  '/citizen':     'Citizen Portal',
  '/settings':    'Settings & Administration',
};

// ─────────────────────────────────────────────────────────────
// APP ROUTES
// ─────────────────────────────────────────────────────────────
const AppRoutes = () => {
  const loc = useLocation();
  const title = TITLES[loc.pathname] || 'AquaPulse';
  const W = ({ page }) => <Guard><Layout title={title}>{page}</Layout></Guard>;
  return (
    <Routes>
      <Route path="/login"      element={<LoginPage />} />
      <Route path="/register"   element={<RegisterPage />} />
      <Route path="/"           element={<W page={<DashboardPage />} />} />
      <Route path="/monitoring" element={<W page={<MonitoringPage />} />} />
      <Route path="/analytics"  element={<W page={<AnalyticsPage />} />} />
      <Route path="/compliance" element={<W page={<CompliancePage />} />} />
      <Route path="/citizen"    element={<W page={<CitizenPage />} />} />
      <Route path="/settings"   element={<W page={<SettingsPage />} />} />
      <Route path="*"           element={<Navigate to="/" replace />} />
    </Routes>
  );
};

// ─────────────────────────────────────────────────────────────
// ROOT APP
// ─────────────────────────────────────────────────────────────
function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <DataProvider>
          <Router>
            <AppRoutes />
            <Toaster
              position="top-right"
              toastOptions={{
                style: { background:'#1e293b', color:'#f1f5f9', border:'1px solid rgba(255,255,255,0.08)', borderRadius:'14px', fontSize:'14px' },
                success: { iconTheme: { primary:'#22c55e', secondary:'#1e293b' } },
                error:   { iconTheme: { primary:'#ef4444', secondary:'#1e293b' } },
              }}
            />
          </Router>
        </DataProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
