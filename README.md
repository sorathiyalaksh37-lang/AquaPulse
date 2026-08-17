# 🌊 AquaPulse - AI-Powered Water Quality Monitoring Platform

A production-ready, multi-page web application for comprehensive water quality monitoring with authentication, real-time analytics, AI-powered predictions, and regulatory compliance reporting.

## 🎯 Project Overview

AquaPulse is an advanced water quality management system designed for government agencies, water utilities, and citizens. It provides real-time monitoring, AI-powered anomaly detection, predictive analytics, and CPCB-compliant reporting.

## ✨ Key Features

### 🔐 Authentication & User Management
- Multi-role authentication (Admin, Government Official, Citizen)
- JWT-based session management
- Password reset and profile management
- Role-based access control

### 📊 Real-Time Monitoring Dashboard
- Live status indicators for water quality
- 6 parameter monitoring (pH, TDS, Turbidity, Temperature, Conductivity, DO)
- Interactive charts and visualizations
- Quick stats cards with animated counters
- Real-time WebSocket updates

### 🤖 AI-Powered Analytics
- **LSTM Forecasting**: 24-hour prediction for all parameters
- **Anomaly Detection**: CNN-BiLSTM and Isolation Forest
- **Predictive Maintenance**: Equipment health monitoring
- **Trend Analysis**: Seasonal pattern detection
- **Explainable AI**: SHAP values for model interpretability

### 📋 Compliance & Reporting
- CPCB BIS 10500:2012 compliant reports
- Automated daily/weekly/monthly reports
- Export to PDF, Excel, and Word formats
- Alert history and resolution tracking

### 👥 Citizen Portal
- Public water quality dashboard
- Issue reporting with photo upload
- Push notifications for safety alerts
- Educational resources

### ⚙️ Administration
- System settings configuration
- User management
- Monitoring node management
- Data retention and backup

## 🏗️ Technology Stack

### Backend
- **Framework**: Flask with SocketIO
- **Authentication**: JWT (Flask-JWT-Extended)
- **Database**: PostgreSQL + Firebase Realtime Database
- **ORM**: SQLAlchemy

### AI/ML
- **Deep Learning**: TensorFlow/Keras (LSTM, CNN-BiLSTM)
- **Machine Learning**: scikit-learn (Isolation Forest), XGBoost
- **Explainability**: SHAP
- **Data Processing**: pandas, NumPy

### Frontend (Coming Soon)
- **Framework**: React.js
- **Styling**: TailwindCSS
- **Charts**: Recharts/D3.js
- **State Management**: Context API/Redux

### Notifications
- **Email**: SendGrid
- **SMS**: Twilio
- **Push**: WebSocket

### Reports
- **PDF**: ReportLab, WeasyPrint
- **Excel**: openpyxl
- **Word**: python-docx

## 📁 Project Structure

```
aquapulse-prototype/
├── backend/
│   ├── models/          # Database models
│   ├── routes/          # API endpoints
│   ├── services/        # Business logic
│   ├── middleware/      # Authentication & authorization
│   └── utils/           # Helper functions
├── frontend/
│   └── src/
│       ├── components/  # Reusable React components
│       ├── pages/       # Page components
│       ├── services/    # API services
│       ├── contexts/    # React contexts
│       └── hooks/       # Custom hooks
├── config/              # Configuration files
├── data/                # Sample data
├── models/              # Trained AI models
├── static/              # Static assets
├── templates/           # HTML templates
├── tests/               # Test files
├── app.py              # Main Flask application
├── ai_model.py         # AI/ML model implementation
├── data_simulator.py   # Data simulation
└── requirements.txt    # Python dependencies
```

## 🚀 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL
- Redis (for Celery task queue)
- Node.js 16+ (for frontend)

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/sorathiyalaksh37-lang/AquaPulse.git
cd AquaPulse
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
python -c "from backend.models import db; from app import app; app.app_context().push(); db.create_all()"
```

6. Run the application:
```bash
python app.py
```

The server will start at `http://localhost:5001`

## 📊 CPCB Standards (BIS 10500:2012)

| Parameter | Safe Range | Unit |
|-----------|------------|------|
| pH | 6.5 - 8.5 | - |
| TDS | 0 - 500 | ppm |
| Turbidity | 0 - 5 | NTU |
| Temperature | 15 - 35 | °C |
| Conductivity | 0 - 1000 | µS/cm |
| Dissolved Oxygen | 5 - 14 | mg/L |

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user profile
- `PUT /api/auth/me` - Update profile
- `POST /api/auth/change-password` - Change password

### Monitoring
- `GET /api/latest` - Get latest reading
- `GET /api/history` - Get historical data
- `GET /api/parameters` - Get parameter definitions
- `GET /api/status` - Get system status

### Alerts
- `GET /api/alerts` - Get all alerts
- `POST /api/alert/<id>` - Resolve alert

### Reports
- `GET /api/generate_report` - Generate CPCB report
- `GET /api/reports` - List all reports

### Simulation (Demo)
- `POST /api/simulate_contamination` - Trigger contamination event
- `POST /api/reset_system` - Reset to normal state

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

## 📝 Configuration

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/aquapulse

# Firebase
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com/
FIREBASE_CREDENTIALS_PATH=./config/firebase-credentials.json

# Notifications
SENDGRID_API_KEY=your-sendgrid-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token

# Sampling
SAMPLING_INTERVAL_HOURS=3
DATA_RETENTION_DAYS=365
```

## 🔒 Security Features

- Password hashing with bcrypt
- JWT token authentication
- Role-based access control (RBAC)
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration
- Input validation and sanitization

## 📈 Monitoring & Performance

- Real-time data updates via WebSocket
- Background task processing with Celery
- Redis caching for improved performance
- Database query optimization
- API rate limiting

## 🎨 UI/UX Features (Frontend - Coming Soon)

- Glassmorphism design aesthetic
- Dark/Light mode toggle
- Responsive design (mobile, tablet, desktop)
- Smooth animations and transitions
- Accessibility (WCAG 2.1 compliant)
- PWA capabilities
- Offline support

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Author

**Laksh Sorathiya**

- GitHub: [@sorathiyalaksh37-lang](https://github.com/sorathiyalaksh37-lang)

## 🙏 Acknowledgments

- CPCB (Central Pollution Control Board) for water quality standards
- BIS 10500:2012 for drinking water specifications
- Open-source community for amazing tools and libraries

## 📞 Support

For support, email lakshsorathiya@example.com or open an issue on GitHub.

---

**Status**: 🚧 Under Active Development

**Version**: 1.0.0-beta

Made with ❤️ for clean water monitoring
