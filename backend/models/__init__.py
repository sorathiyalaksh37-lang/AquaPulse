"""Database models"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Import models
from .user import User
from .reading import Reading
from .alert import Alert
from .node import MonitoringNode
from .report import Report
from .citizen_report import CitizenReport

__all__ = ['db', 'User', 'Reading', 'Alert', 'MonitoringNode', 'Report', 'CitizenReport']
