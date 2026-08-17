"""Application configuration"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///aquapulse.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', './config/firebase-credentials.json')
    FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL', '')
    
    # Email
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@aquapulse.com')
    
    # SMS
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Application
    APP_NAME = os.getenv('APP_NAME', 'AquaPulse')
    APP_URL = os.getenv('APP_URL', 'http://localhost:5001')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    # Sampling
    SAMPLING_INTERVAL_HOURS = int(os.getenv('SAMPLING_INTERVAL_HOURS', 3))
    DATA_RETENTION_DAYS = int(os.getenv('DATA_RETENTION_DAYS', 365))
    
    # Alerts
    ALERT_EMAIL_ENABLED = os.getenv('ALERT_EMAIL_ENABLED', 'true').lower() == 'true'
    ALERT_SMS_ENABLED = os.getenv('ALERT_SMS_ENABLED', 'true').lower() == 'true'
    ALERT_PUSH_ENABLED = os.getenv('ALERT_PUSH_ENABLED', 'true').lower() == 'true'
    
    # Reports
    REPORTS_DIR = os.getenv('REPORTS_DIR', './reports')
    TEMP_DIR = os.getenv('TEMP_DIR', './temp')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5001').split(',')
    
    # CPCB Standards (BIS 10500:2012)
    CPCB_STANDARDS = {
        'pH': {'min': 6.5, 'max': 8.5, 'unit': '', 'name': 'pH Level'},
        'tds': {'min': 0, 'max': 500, 'unit': 'ppm', 'name': 'Total Dissolved Solids'},
        'turbidity': {'min': 0, 'max': 5, 'unit': 'NTU', 'name': 'Turbidity'},
        'temperature': {'min': 15, 'max': 35, 'unit': '°C', 'name': 'Temperature'},
        'conductivity': {'min': 0, 'max': 1000, 'unit': 'µS/cm', 'name': 'Conductivity'},
        'dissolved_oxygen': {'min': 5, 'max': 14, 'unit': 'mg/L', 'name': 'Dissolved Oxygen'}
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_aquapulse.db'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
