"""
认证路由模块
处理用户注册、登录、登出、个人信息管理
"""
from flask import Blueprint, request
from datetime import timedelta
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User
from app.utils import success_response, error_response

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    # 验证必填字段
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return error_response('Missing required fields: username, email, password', 400)
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return error_response('Username already exists', 409)
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=data['email']).first():
        return error_response('Email already exists', 409)
    
    # 创建新用户
    try:
        new_user = User(
            username=data['username'],
            email=data['email'],
            phone=data.get('phone'),
            address=data.get('address')
        )
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        return success_response(
            data={'user': new_user.to_dict()},
            message='User registered successfully',
            code=201
        )
    except Exception as e:
        db.session.rollback()
        return error_response(f'Registration failed: {str(e)}', 500)


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return error_response('Missing username or password', 400)
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return error_response('Invalid username or password', 401)
    
    if not user.is_active:
        return error_response('User account is disabled', 401)
    
    # 更新最后登录时间
    user.update_last_login()
    
    # 生成 JWT token
    access_token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(days=1),
        additional_claims={
            'username': user.username,
            'is_admin': user.is_admin
        }
    )
    
    return success_response({
        'token': access_token,
        'token_type': 'Bearer',
        'expires_in': 86400,
        'user': user.to_dict()
    }, 'Login successful')


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """刷新访问令牌"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return error_response('User not found or disabled', 401)
    
    new_token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(days=1)
    )
    
    return success_response({
        'token': new_token,
        'token_type': 'Bearer',
        'expires_in': 86400
    })


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户信息"""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    return success_response({'user': user.to_dict()})


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户信息"""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()
    
    try:
        if data.get('phone'):
            user.phone = data['phone']
        if data.get('address'):
            user.address = data['address']
        if data.get('avatar_url'):
            user.avatar_url = data['avatar_url']
        if data.get('email'):
            # 检查新邮箱是否已被其他用户使用
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user.id:
                return error_response('Email already in use', 409)
            user.email = data['email']
        
        db.session.commit()
        
        return success_response({
            'user': user.to_dict()
        }, 'Profile updated successfully')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Update failed: {str(e)}', 500)


@auth_bp.route('/password', methods=['PUT'])
@jwt_required()
def change_password():
    """修改密码"""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()
    
    if not data or not data.get('old_password') or not data.get('new_password'):
        return error_response('Old password and new password are required', 400)
    
    if not user.check_password(data['old_password']):
        return error_response('Old password is incorrect', 401)
    
    try:
        user.set_password(data['new_password'])
        db.session.commit()
        return success_response(message='Password changed successfully')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Password change failed: {str(e)}', 500)
