"""购物车模型"""
from datetime import datetime
from app.extensions import db


class CartItem(db.Model):
    """购物车项"""
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    sku_id = db.Column(db.Integer, db.ForeignKey('product_skus.id'))
    quantity = db.Column(db.Integer, default=1)
    is_selected = db.Column(db.Boolean, default=True)  # 是否选中
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        product = self.product
        sku = self.sku if self.sku_id else None
        
        # 使用SKU价格（如果有）否则使用商品价格
        price = sku.price if sku else product.price
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'sku_id': self.sku_id,
            'quantity': self.quantity,
            'is_selected': self.is_selected,
            'product': product.to_dict() if product else None,
            'sku': sku.to_dict() if sku else None,
            'price': float(price) if price else 0,
            'total_price': float(price * self.quantity) if price else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def update_quantity(self, quantity):
        """更新数量"""
        if quantity < 1:
            raise ValueError('数量必须大于0')
        
        # 检查库存
        product = self.product
        if product and quantity > product.stock:
            raise ValueError('库存不足')
        
        self.quantity = quantity
    
    def __repr__(self):
        return f'<CartItem {self.id}>'
