"""商品相关模型"""
from datetime import datetime
from app.extensions import db


class Category(db.Model):
    """商品分类模型"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    icon_url = db.Column(db.String(500))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 自关联 - 父子分类
    parent = db.relationship('Category', remote_side=[id], backref='children')
    products = db.relationship('Product', backref='category', lazy='dynamic')
    
    def to_dict(self, include_children=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon_url': self.icon_url,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_children and self.children:
            data['children'] = [child.to_dict() for child in self.children]
        
        return data
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    """商品模型"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Decimal(10, 2), nullable=False)
    original_price = db.Column(db.Decimal(10, 2))
    stock = db.Column(db.Integer, default=0)
    sales_count = db.Column(db.Integer, default=0)
    main_image = db.Column(db.String(500))
    images = db.Column(db.JSON)  # 图片列表
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), index=True)
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)  # 是否推荐
    weight = db.Column(db.Decimal(8, 2))  # 重量(kg)
    unit = db.Column(db.String(20), default='件')  # 单位
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')
    cart_items = db.relationship('CartItem', backref='product', lazy='dynamic')
    reviews = db.relationship('Review', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    skus = db.relationship('ProductSKU', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_details=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else 0,
            'original_price': float(self.original_price) if self.original_price else None,
            'stock': self.stock,
            'sales_count': self.sales_count,
            'main_image': self.main_image,
            'category_id': self.category_id,
            'category': self.category.name if self.category else None,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'weight': float(self.weight) if self.weight else None,
            'unit': self.unit,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_details:
            data['images'] = self.images
            data['skus'] = [sku.to_dict() for sku in self.skus] if self.skus else []
            data['reviews_count'] = self.reviews.count()
        
        return data
    
    def decrease_stock(self, quantity):
        """减少库存"""
        if self.stock < quantity:
            raise ValueError('库存不足')
        self.stock -= quantity
        self.sales_count += quantity
    
    def __repr__(self):
        return f'<Product {self.name}>'


class ProductSKU(db.Model):
    """商品SKU模型（规格）"""
    __tablename__ = 'product_skus'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    sku_code = db.Column(db.String(100), unique=True, nullable=False)
    attributes = db.Column(db.JSON)  # 规格属性，如 {"颜色": "红色", "尺码": "XL"}
    price = db.Column(db.Decimal(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sku_code': self.sku_code,
            'attributes': self.attributes,
            'price': float(self.price) if self.price else 0,
            'stock': self.stock,
            'image_url': self.image_url,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<ProductSKU {self.sku_code}>'


class Review(db.Model):
    """商品评价模型"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5星
    content = db.Column(db.Text)
    images = db.Column(db.JSON)
    is_anonymous = db.Column(db.Boolean, default=False)
    is_show = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'user': {
                'id': self.user_id,
                'username': '匿名用户' if self.is_anonymous else self.user.username,
                'avatar_url': None if self.is_anonymous else self.user.avatar_url
            },
            'rating': self.rating,
            'content': self.content,
            'images': self.images,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
