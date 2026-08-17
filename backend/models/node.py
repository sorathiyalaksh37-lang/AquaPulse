"""Monitoring Node model"""
from . import db
from datetime import datetime
import json

class MonitoringNode(db.Model):
    """Monitoring node/station model"""
    __tablename__ = 'monitoring_nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    ward = db.Column(db.String(50))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    # Node details
    node_type = db.Column(db.String(50), default='water_quality')  # water_quality, treatment_plant, reservoir
    status = db.Column(db.String(20), default='active')  # active, inactive, maintenance
    hardware_id = db.Column(db.String(100), unique=True)
    firmware_version = db.Column(db.String(20))
    
    # Equipment health
    equipment_health = db.Column(db.Text)  # JSON with sensor health
    last_calibration = db.Column(db.DateTime)
    next_maintenance = db.Column(db.DateTime)
    
    # Metadata
    description = db.Column(db.Text)
    installed_at = db.Column(db.DateTime)
    is_public = db.Column(db.Boolean, default=True)  # Visible to citizens
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    readings = db.relationship('Reading', backref='node', lazy='dynamic')
    alerts = db.relationship('Alert', backref='node', lazy='dynamic')
    
    def set_equipment_health(self, health_dict):
        """Set equipment health as JSON"""
        self.equipment_health = json.dumps(health_dict)
    
    def get_equipment_health(self):
        """Get equipment health from JSON"""
        if self.equipment_health:
            return json.loads(self.equipment_health)
        return {
            'filter': {'health': 100, 'status': 'good'},
            'pump': {'health': 100, 'status': 'good'},
            'sensor': {'health': 100, 'status': 'good'}
        }
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'ward': self.ward,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'node_type': self.node_type,
            'status': self.status,
            'hardware_id': self.hardware_id,
            'firmware_version': self.firmware_version,
            'equipment_health': self.get_equipment_health(),
            'last_calibration': self.last_calibration.isoformat() if self.last_calibration else None,
            'next_maintenance': self.next_maintenance.isoformat() if self.next_maintenance else None,
            'description': self.description,
            'installed_at': self.installed_at.isoformat() if self.installed_at else None,
            'is_public': self.is_public
        }
    
    def __repr__(self):
        return f'<MonitoringNode {self.name}>'
