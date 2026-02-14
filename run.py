"""
应用启动脚本
用于开发和调试
"""
import os
from app import create_app, db
from app.models import User, Category, Product, Order, CartItem

# 创建应用实例
app = create_app(os.environ.get('FLASK_ENV', 'development'))

# Shell 上下文
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Category': Category,
        'Product': Product,
        'Order': Order,
        'CartItem': CartItem
    }


if __name__ == '__main__':
    with app.app_context():
        # 自动创建数据表
        db.create_all()
        print("Database tables created!")
    
    # 启动开发服务器
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True
    )
