"""Report model"""
from . import db
from datetime import datetime

class Report(db.Model):
    """Report model for compliance and automated reports"""
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    report_type = db.Column(db.String(50), nullable=False)  # cpcb, daily, weekly, monthly, custom
    title = db.Column(db.String(200), nullable=False)
    
    # Report details
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Report data
    report_data = db.Column(db.Text)  # JSON string with all report data
    summary = db.Column(db.Text)
    compliance_score = db.Column(db.Float)
    
    # Files
    pdf_path = db.Column(db.String(255))
    excel_path = db.Column(db.String(255))
    word_path = db.Column(db.String(255))
    
    # Status
    status = db.Column(db.String(20), default='generated')  # generated, sent, archived
    is_automated = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'report_id': self.report_id,
            'report_type': self.report_type,
            'title': self.title,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'compliance_score': self.compliance_score,
            'status': self.status,
            'is_automated': self.is_automated,
            'files': {
                'pdf': self.pdf_path,
                'excel': self.excel_path,
                'word': self.word_path
            }
        }
    
    def __repr__(self):
        return f'<Report {self.report_id}>'
