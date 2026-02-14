"""路由模块初始化"""
from app.routes.auth import auth_bp
from app.routes.products import products_bp
from app.routes.orders import orders_bp
from app.routes.users import users_bp

__all__ = [
    'auth_bp',
    'products_bp',
    'orders_bp',
    'users_bp'
]
