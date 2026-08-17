"""Authentication middleware"""
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from backend.models import User, db

def jwt_required_custom(fn):
    """Custom JWT required decorator"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': 'Invalid or expired token', 'message': str(e)}), 401
    return wrapper

def get_current_user():
    """Get current user from JWT"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return user
    except:
        return None

def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user = get_current_user()
                
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                if not user.is_active:
                    return jsonify({'error': 'Account is inactive'}), 403
                
                if user.role not in roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                return fn(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': 'Authorization failed', 'message': str(e)}), 401
        return wrapper
    return decorator

def admin_required(fn):
    """Decorator to require admin role"""
    return role_required('admin')(fn)

def government_or_admin_required(fn):
    """Decorator to require government or admin role"""
    return role_required('admin', 'government')(fn)
