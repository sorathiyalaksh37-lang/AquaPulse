"""User model"""
from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='citizen')  # admin, government, citizen
    phone = db.Column(db.String(20))
    organization = db.Column(db.String(100))
    ward = db.Column(db.String(50))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    notification_preferences = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    citizen_reports = db.relationship('CitizenReport', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def set_notification_preferences(self, preferences):
        """Set notification preferences"""
        self.notification_preferences = json.dumps(preferences)
    
    def get_notification_preferences(self):
        """Get notification preferences"""
        if self.notification_preferences:
            return json.loads(self.notification_preferences)
        return {'email': True, 'sms': False, 'push': True}
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'phone': self.phone,
            'organization': self.organization,
            'ward': self.ward,
            'address': self.address,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'notification_preferences': self.get_notification_preferences(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.email}>'
