"""
用户管理路由模块
处理用户查询、管理（管理员）
"""
from flask import Blueprint, request

from app.extensions import db
from app.models import User, Order
from app.utils import token_required, admin_required, success_response, error_response, paginated_response

users_bp = Blueprint('users', __name__)


@users_bp.route('/', methods=['GET'])
@token_required
@admin_required
def get_users(current_user):
    """获取用户列表（管理员）"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search = request.args.get('q', '')
    is_admin = request.args.get('is_admin', type=bool)
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    if is_admin is not None:
        query = query.filter_by(is_admin=is_admin)
    
    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return paginated_response(
        items=[u.to_dict() for u in pagination.items],
        total=pagination.total,
        page=page,
        per_page=per_page,
        pages=pagination.pages
    )


@users_bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    """获取用户详情"""
    if not current_user.is_admin and current_user.id != user_id:
        return error_response('Access denied', 403)
    
    user = User.query.get_or_404(user_id)
    return success_response({'user': user.to_dict(include_sensitive=current_user.is_admin)})


@users_bp.route('/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(current_user, user_id):
    """更新用户信息（管理员）"""
    if current_user.id == user_id:
        return error_response('Use profile API to update your own info', 400)
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    try:
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
        if 'phone' in data:
            user.phone = data['phone']
        if 'address' in data:
            user.address = data['address']
        
        db.session.commit()
        
        return success_response({
            'user': user.to_dict()
        }, 'User updated successfully')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Update failed: {str(e)}', 500)


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(current_user, user_id):
    """删除用户（管理员）"""
    if current_user.id == user_id:
        return error_response('Cannot delete yourself', 400)
    
    user = User.query.get_or_404(user_id)
    
    try:
        # 软删除：禁用用户而不是真正删除
        user.is_active = False
        db.session.commit()
        return success_response(message='User disabled successfully')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Deletion failed: {str(e)}', 500)


@users_bp.route('/<int:user_id>/orders', methods=['GET'])
@token_required
def get_user_orders(current_user, user_id):
    """获取用户订单列表"""
    if not current_user.is_admin and current_user.id != user_id:
        return error_response('Access denied', 403)
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    
    query = Order.query.filter_by(user_id=user_id)
    
    if status:
        query = query.filter_by(status=status)
    
    query = query.order_by(Order.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return paginated_response(
        items=[o.to_dict() for o in pagination.items],
        total=pagination.total,
        page=page,
        per_page=per_page,
        pages=pagination.pages
    )


# ==================== 管理员订单管理 ====================

@users_bp.route('/orders', methods=['GET'])
@token_required
@admin_required
def get_all_orders(current_user):
    """获取所有订单（管理员）"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    user_id = request.args.get('user_id', type=int)
    
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    query = query.order_by(Order.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return paginated_response(
        items=[o.to_dict(include_items=True) for o in pagination.items],
        total=pagination.total,
        page=page,
        per_page=per_page,
        pages=pagination.pages
    )


@users_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@token_required
@admin_required
def update_order_status(current_user, order_id):
    """更新订单状态（管理员）"""
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    
    if not data or not data.get('status'):
        return error_response('Status is required', 400)
    
    new_status = data['status']
    valid_statuses = [
        Order.STATUS_PENDING, Order.STATUS_PAID, Order.STATUS_SHIPPED,
        Order.STATUS_DELIVERED, Order.STATUS_COMPLETED, Order.STATUS_CANCELLED,
        Order.STATUS_REFUNDING, Order.STATUS_REFUNDED
    ]
    
    if new_status not in valid_statuses:
        return error_response('Invalid status', 400)
    
    try:
        # 根据状态更新相应的时间字段
        if new_status == Order.STATUS_PAID and order.status == Order.STATUS_PENDING:
            order.paid_at = datetime.utcnow()
        elif new_status == Order.STATUS_SHIPPED and order.status in [Order.STATUS_PENDING, Order.STATUS_PAID]:
            order.shipped_at = datetime.utcnow()
            if data.get('express_company'):
                order.express_company = data['express_company']
            if data.get('express_number'):
                order.express_number = data['express_number']
        elif new_status == Order.STATUS_DELIVERED:
            order.delivered_at = datetime.utcnow()
        elif new_status == Order.STATUS_COMPLETED:
            order.completed_at = datetime.utcnow()
        
        order.status = new_status
        db.session.commit()
        
        return success_response({
            'order': order.to_dict()
        }, 'Order status updated')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Update failed: {str(e)}', 500)


@users_bp.route('/orders/<int:order_id>', methods=['GET'])
@token_required
@admin_required
def get_order_detail(current_user, order_id):
    """获取订单详情（管理员）"""
    order = Order.query.get_or_404(order_id)
    return success_response({'order': order.to_dict(include_items=True)})
