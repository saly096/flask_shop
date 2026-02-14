"""
Flask 应用工厂模块
创建和配置 Flask 应用实例
"""
from flask import Flask, jsonify
from datetime import datetime
import os

from app.config import config
from app.extensions import db, cors, jwt, migrate, ma
from app.routes import auth_bp, products_bp, orders_bp, users_bp


def create_app(config_name=None):
    """
    应用工厂函数
    
    Args:
        config_name: 配置环境名称 (development/testing/production)
    
    Returns:
        Flask: 配置好的 Flask 应用实例
    """
    # 从环境变量获取配置，默认为 development
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化配置
    config[config_name].init_app(app)
    
    # 初始化扩展
    register_extensions(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册错误处理
    register_error_handlers(app)
    
    # 注册 CLI 命令
    register_commands(app)
    
    # 健康检查路由
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Welcome to Flask Shop API',
            'version': '2.0.0',
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    return app


def register_extensions(app):
    """注册 Flask 扩展"""
    db.init_app(app)
    cors.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)


def register_blueprints(app):
    """注册路由蓝图"""
    # API 版本前缀
    api_prefix = '/api/v1'
    
    app.register_blueprint(auth_bp, url_prefix=f'{api_prefix}/auth')
    app.register_blueprint(products_bp, url_prefix=f'{api_prefix}/products')
    app.register_blueprint(orders_bp, url_prefix=f'{api_prefix}/orders')
    app.register_blueprint(users_bp, url_prefix=f'{api_prefix}/users')


def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'message': 'Bad request',
            'error': str(error.description) if hasattr(error, 'description') else 'Invalid request'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'message': 'Unauthorized',
            'error': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'message': 'Forbidden',
            'error': 'Permission denied'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Not found',
            'error': 'Resource not found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'message': 'Method not allowed',
            'error': 'HTTP method not supported'
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error': 'Something went wrong'
        }), 500


def register_commands(app):
    """注册 CLI 命令"""
    from app.models import User
    
    @app.cli.command('init-db')
    def init_db():
        """初始化数据库"""
        with app.app_context():
            db.create_all()
            print('Database initialized successfully!')
    
    @app.cli.command('drop-db')
    def drop_db():
        """删除所有数据表"""
        with app.app_context():
            db.drop_all()
            print('Database dropped successfully!')
    
    @app.cli.command('create-admin')
    def create_admin():
        """创建管理员用户"""
        import click
        
        username = click.prompt('Admin username')
        email = click.prompt('Admin email')
        password = click.prompt('Admin password', hide_input=True)
        
        with app.app_context():
            if User.query.filter_by(username=username).first():
                print(f'User {username} already exists!')
                return
            
            admin = User(
                username=username,
                email=email,
                is_admin=True
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f'Admin user {username} created successfully!')
