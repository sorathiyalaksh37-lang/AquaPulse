"""Alert model"""
from . import db
from datetime import datetime

class Alert(db.Model):
    """Alert model for water quality issues"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    reading_id = db.Column(db.Integer, db.ForeignKey('readings.id'))
    node_id = db.Column(db.Integer, db.ForeignKey('monitoring_nodes.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Alert details
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    alert_type = db.Column(db.String(50), nullable=False)  # contamination, anomaly, equipment, threshold
    message = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    
    # Affected parameters
    affected_parameters = db.Column(db.Text)  # JSON array
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, acknowledged, resolved
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledged_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    
    # Notifications
    email_sent = db.Column(db.Boolean, default=False)
    sms_sent = db.Column(db.Boolean, default=False)
    push_sent = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'reading_id': self.reading_id,
            'node_id': self.node_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'severity': self.severity,
            'alert_type': self.alert_type,
            'message': self.message,
            'description': self.description,
            'status': self.status,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_notes': self.resolution_notes,
            'notifications': {
                'email_sent': self.email_sent,
                'sms_sent': self.sms_sent,
                'push_sent': self.push_sent
            }
        }
    
    def __repr__(self):
        return f'<Alert {self.id} - {self.severity}>'
