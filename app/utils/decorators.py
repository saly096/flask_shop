"""认证装饰器和工具函数"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User


def token_required(fn):
    """JWT Token 验证装饰器"""
    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)
            
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
            
            if not current_user.is_active:
                return jsonify({'message': 'User account is disabled'}), 401
            
            return fn(current_user, *args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Invalid token', 'error': str(e)}), 401
    
    return decorator


def admin_required(fn):
    """管理员权限验证装饰器"""
    @wraps(fn)
    def decorator(current_user, *args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'message': 'Admin access required'}), 403
        return fn(current_user, *args, **kwargs)
    
    return decorator
