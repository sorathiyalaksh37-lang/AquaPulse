"""Reading model"""
from . import db
from datetime import datetime
import json

class Reading(db.Model):
    """Water quality reading model"""
    __tablename__ = 'readings'
    
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.Integer, db.ForeignKey('monitoring_nodes.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Water quality parameters
    ph = db.Column(db.Float, nullable=False)
    tds = db.Column(db.Float, nullable=False)
    turbidity = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    conductivity = db.Column(db.Float, nullable=False)
    dissolved_oxygen = db.Column(db.Float, nullable=False)
    
    # Status
    overall_status = db.Column(db.String(20))  # Safe, Caution, Unsafe
    is_anomaly = db.Column(db.Boolean, default=False)
    anomaly_score = db.Column(db.Float)
    
    # Metadata
    parameters_status = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_parameters_status(self, status_dict):
        """Set parameters status as JSON"""
        self.parameters_status = json.dumps(status_dict)
    
    def get_parameters_status(self):
        """Get parameters status from JSON"""
        if self.parameters_status:
            return json.loads(self.parameters_status)
        return {}
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'node_id': self.node_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'parameters': {
                'pH': self.ph,
                'tds': self.tds,
                'turbidity': self.turbidity,
                'temperature': self.temperature,
                'conductivity': self.conductivity,
                'dissolved_oxygen': self.dissolved_oxygen
            },
            'overall_status': self.overall_status,
            'is_anomaly': self.is_anomaly,
            'anomaly_score': self.anomaly_score,
            'status': self.get_parameters_status()
        }
    
    def __repr__(self):
        return f'<Reading {self.id} at {self.timestamp}>'
