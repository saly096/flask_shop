"""测试配置和初始化"""
import pytest
from app import create_app, db
from app.models import User, Category, Product


@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建 CLI 测试 runner"""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers(app):
    """创建认证 headers"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=user.id)
        
        return {'Authorization': f'Bearer {token}'}
