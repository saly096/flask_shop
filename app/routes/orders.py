"""
订单路由模块
处理购物车、订单创建、订单管理
"""
import random
import string
from datetime import datetime
from flask import Blueprint, request

from app.extensions import db
from app.models import Order, OrderItem, CartItem, Product
from app.utils import token_required, success_response, error_response, paginated_response

orders_bp = Blueprint('orders', __name__)


def generate_order_number():
    """生成订单号: ORD + 年月日时分秒 + 4位随机码"""
    prefix = 'ORD'
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}{timestamp}{random_str}"


# ==================== 购物车 ====================

@orders_bp.route('/cart', methods=['GET'])
@token_required
def get_cart(current_user):
    """获取购物车"""
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    # 计算总价
    total_amount = sum(
        item.to_dict()['total_price'] for item in cart_items if item.is_selected
    )
    
    return success_response({
        'cart_items': [item.to_dict() for item in cart_items],
        'total_amount': total_amount,
        'total_count': len(cart_items),
        'selected_count': sum(1 for item in cart_items if item.is_selected)
    })


@orders_bp.route('/cart', methods=['POST'])
@token_required
def add_to_cart(current_user):
    """添加商品到购物车"""
    data = request.get_json()
    
    if not data or not data.get('product_id') or not data.get('quantity'):
        return error_response('Product ID and quantity are required', 400)
    
    product = Product.query.get_or_404(data['product_id'])
    sku_id = data.get('sku_id')
    quantity = data['quantity']
    
    if product.stock < quantity:
        return error_response(f'Insufficient stock. Available: {product.stock}', 400)
    
    try:
        # 检查购物车中是否已有该商品
        cart_item = CartItem.query.filter_by(
            user_id=current_user.id,
            product_id=data['product_id'],
            sku_id=sku_id
        ).first()
        
        if cart_item:
            # 更新数量
            new_quantity = cart_item.quantity + quantity
            if product.stock < new_quantity:
                return error_response(f'Insufficient stock. Available: {product.stock}', 400)
            cart_item.quantity = new_quantity
        else:
            cart_item = CartItem(
                user_id=current_user.id,
                product_id=data['product_id'],
                sku_id=sku_id,
                quantity=quantity
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        return success_response({
            'cart_item': cart_item.to_dict()
        }, 'Item added to cart')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Failed to add to cart: {str(e)}', 500)


@orders_bp.route('/cart/<int:item_id>', methods=['PUT'])
@token_required
def update_cart_item(current_user, item_id):
    """更新购物车项"""
    data = request.get_json()
    cart_item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    
    try:
        if 'quantity' in data:
            if data['quantity'] <= 0:
                db.session.delete(cart_item)
                db.session.commit()
                return success_response(message='Item removed from cart')
            
            # 检查库存
            product = cart_item.product
            if product.stock < data['quantity']:
                return error_response(f'Insufficient stock. Available: {product.stock}', 400)
            
            cart_item.quantity = data['quantity']
        
        if 'is_selected' in data:
            cart_item.is_selected = data['is_selected']
        
        db.session.commit()
        
        return success_response({
            'cart_item': cart_item.to_dict()
        }, 'Cart updated')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Update failed: {str(e)}', 500)


@orders_bp.route('/cart/<int:item_id>', methods=['DELETE'])
@token_required
def remove_from_cart(current_user, item_id):
    """从购物车移除商品"""
    cart_item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(cart_item)
        db.session.commit()
        return success_response(message='Item removed from cart')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Removal failed: {str(e)}', 500)


@orders_bp.route('/cart/clear', methods=['DELETE'])
@token_required
def clear_cart(current_user):
    """清空购物车"""
    try:
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return success_response(message='Cart cleared')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Clear failed: {str(e)}', 500)


# ==================== 订单管理 ====================

@orders_bp.route('/', methods=['POST'])
@token_required
def create_order(current_user):
    """创建订单"""
    data = request.get_json() or {}
    
    # 获取购物车选中项或指定商品
    cart_item_ids = data.get('cart_item_ids', [])
    
    if cart_item_ids:
        cart_items = CartItem.query.filter(
            CartItem.id.in_(cart_item_ids),
            CartItem.user_id == current_user.id,
            CartItem.is_selected == True
        ).all()
    else:
        cart_items = CartItem.query.filter_by(
            user_id=current_user.id,
            is_selected=True
        ).all()
    
    if not cart_items:
        return error_response('No items selected in cart', 400)
    
    try:
        # 计算订单总额并检查库存
        total_amount = 0
        freight_amount = data.get('freight_amount', 0)
        discount_amount = data.get('discount_amount', 0)
        
        for item in cart_items:
            product = item.product
            if product.stock < item.quantity:
                return error_response(
                    f'Insufficient stock for {product.name}. Available: {product.stock}',
                    400
                )
            # 使用SKU价格如果有SKU，否则使用商品价格
            price = item.sku.price if item.sku else product.price
            total_amount += float(price) * item.quantity
        
        pay_amount = total_amount + freight_amount - discount_amount
        
        # 创建订单
        order = Order(
            user_id=current_user.id,
            order_number=generate_order_number(),
            total_amount=total_amount,
            freight_amount=freight_amount,
            discount_amount=discount_amount,
            pay_amount=pay_amount,
            receiver_name=data.get('receiver_name', current_user.username),
            receiver_phone=data.get('receiver_phone', current_user.phone),
            receiver_address=data.get('receiver_address', current_user.address),
            note=data.get('note')
        )
        
        db.session.add(order)
        db.session.flush()  # 获取 order.id
        
        # 创建订单项
        for cart_item in cart_items:
            product = cart_item.product
            price = cart_item.sku.price if cart_item.sku else product.price
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                sku_id=cart_item.sku_id,
                product_name=product.name,
                product_image=product.main_image,
                sku_attributes=cart_item.sku.attributes if cart_item.sku else None,
                quantity=cart_item.quantity,
                price=price,
                total_price=float(price) * cart_item.quantity
            )
            db.session.add(order_item)
            
            # 减少库存
            product.decrease_stock(cart_item.quantity)
            
            # 删除购物车项
            db.session.delete(cart_item)
        
        db.session.commit()
        
        return success_response({
            'order': order.to_dict(include_items=True)
        }, 'Order created successfully', 201)
    
    except Exception as e:
        db.session.rollback()
        return error_response(f'Order creation failed: {str(e)}', 500)


@orders_bp.route('/', methods=['GET'])
@token_required
def get_orders(current_user):
    """获取订单列表"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    
    query = Order.query.filter_by(user_id=current_user.id)
    
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


@orders_bp.route('/<int:order_id>', methods=['GET'])
@token_required
def get_order(current_user, order_id):
    """获取订单详情"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return success_response({'order': order.to_dict(include_items=True)})


@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
@token_required
def cancel_order(current_user, order_id):
    """取消订单"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    if not order.can_cancel():
        return error_response(f'Cannot cancel order with status: {order.get_status_text()}', 400)
    
    data = request.get_json() or {}
    
    try:
        order.status = Order.STATUS_CANCELLED
        order.cancel_reason = data.get('reason', 'User cancelled')
        
        # 恢复库存
        for item in order.items:
            item.product.stock += item.quantity
        
        db.session.commit()
        
        return success_response({
            'order': order.to_dict()
        }, 'Order cancelled successfully')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Cancel failed: {str(e)}', 500)


@orders_bp.route('/<int:order_id>/confirm', methods=['POST'])
@token_required
def confirm_receipt(current_user, order_id):
    """确认收货"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    
    if order.status != Order.STATUS_SHIPPED and order.status != Order.STATUS_DELIVERED:
        return error_response('Order cannot be confirmed', 400)
    
    try:
        order.status = Order.STATUS_COMPLETED
        order.completed_at = datetime.utcnow()
        db.session.commit()
        
        return success_response({
            'order': order.to_dict()
        }, 'Order confirmed successfully')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Confirmation failed: {str(e)}', 500)
