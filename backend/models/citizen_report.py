"""Citizen Report model"""
from . import db
from datetime import datetime

class CitizenReport(db.Model):
    """Citizen-submitted water quality issue reports"""
    __tablename__ = 'citizen_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Issue details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # taste, odor, color, pressure, other
    severity = db.Column(db.String(20), default='medium')  # low, medium, high
    
    # Location
    location = db.Column(db.String(200))
    ward = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Media
    photo_path = db.Column(db.String(255))
    
    # Status
    status = db.Column(db.String(20), default='submitted')  # submitted, investigating, resolved, closed
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_citizen_report_assigned'))
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    
    # Response
    response = db.Column(db.Text)
    response_by = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_citizen_report_response'))
    response_at = db.Column(db.DateTime)
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime)
    
    # Visibility
    is_public = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'severity': self.severity,
            'location': self.location,
            'ward': self.ward,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'photo_path': self.photo_path,
            'status': self.status,
            'priority': self.priority,
            'response': self.response,
            'response_at': self.response_at.isoformat() if self.response_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'is_public': self.is_public
        }
    
    def __repr__(self):
        return f'<CitizenReport {self.id} - {self.title}>'
