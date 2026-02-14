"""订单相关模型"""
from datetime import datetime
from app.extensions import db


class Order(db.Model):
    """订单模型"""
    __tablename__ = 'orders'
    
    # 订单状态
    STATUS_PENDING = 'pending'           # 待支付
    STATUS_PAID = 'paid'                 # 已支付
    STATUS_SHIPPED = 'shipped'           # 已发货
    STATUS_DELIVERED = 'delivered'       # 已送达
    STATUS_COMPLETED = 'completed'       # 已完成
    STATUS_CANCELLED = 'cancelled'       # 已取消
    STATUS_REFUNDING = 'refunding'       # 退款中
    STATUS_REFUNDED = 'refunded'         # 已退款
    
    # 支付类型
    PAYMENT_WECHAT = 'wechat'
    PAYMENT_ALIPAY = 'alipay'
    PAYMENT_CARD = 'card'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # 金额信息
    total_amount = db.Column(db.Decimal(10, 2), nullable=False)
    discount_amount = db.Column(db.Decimal(10, 2), default=0)
    freight_amount = db.Column(db.Decimal(10, 2), default=0)
    pay_amount = db.Column(db.Decimal(10, 2), nullable=False)
    
    # 状态信息
    status = db.Column(db.String(20), default=STATUS_PENDING, index=True)
    payment_type = db.Column(db.String(20))
    paid_at = db.Column(db.DateTime)
    shipped_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # 收货信息
    receiver_name = db.Column(db.String(100))
    receiver_phone = db.Column(db.String(20))
    receiver_address = db.Column(db.Text)
    
    # 物流信息
    express_company = db.Column(db.String(50))
    express_number = db.Column(db.String(100))
    
    # 其他
    note = db.Column(db.Text)
    cancel_reason = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='order', lazy='dynamic')
    
    def to_dict(self, include_items=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'order_number': self.order_number,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'freight_amount': float(self.freight_amount) if self.freight_amount else 0,
            'pay_amount': float(self.pay_amount) if self.pay_amount else 0,
            'status': self.status,
            'status_text': self.get_status_text(),
            'payment_type': self.payment_type,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'shipped_at': self.shipped_at.isoformat() if self.shipped_at else None,
            'receiver_name': self.receiver_name,
            'receiver_phone': self.receiver_phone,
            'receiver_address': self.receiver_address,
            'express_company': self.express_company,
            'express_number': self.express_number,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        
        return data
    
    def get_status_text(self):
        """获取状态文本"""
        status_map = {
            self.STATUS_PENDING: '待支付',
            self.STATUS_PAID: '已支付',
            self.STATUS_SHIPPED: '已发货',
            self.STATUS_DELIVERED: '已送达',
            self.STATUS_COMPLETED: '已完成',
            self.STATUS_CANCELLED: '已取消',
            self.STATUS_REFUNDING: '退款中',
            self.STATUS_REFUNDED: '已退款'
        }
        return status_map.get(self.status, '未知状态')
    
    def can_cancel(self):
        """是否可以取消"""
        return self.status in [self.STATUS_PENDING, self.STATUS_PAID]
    
    def can_refund(self):
        """是否可以退款"""
        return self.status in [self.STATUS_PAID, self.STATUS_SHIPPED, self.STATUS_DELIVERED]
    
    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    """订单商品项"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    
    # 商品快照信息（防止商品修改后订单信息变化）
    product_name = db.Column(db.String(200), nullable=False)
    product_image = db.Column(db.String(500))
    sku_attributes = db.Column(db.JSON)
    
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Decimal(10, 2), nullable=False)  # 下单时的价格
    total_price = db.Column(db.Decimal(10, 2), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_image': self.product_image,
            'sku_id': self.sku_id,
            'sku_attributes': self.sku_attributes,
            'quantity': self.quantity,
            'price': float(self.price) if self.price else 0,
            'total_price': float(self.total_price) if self.total_price else 0,
            'product': self.product.to_dict() if self.product else None
        }
