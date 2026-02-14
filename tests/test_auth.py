"""认证模块测试"""
import json


def test_register_success(client):
    """测试用户注册成功"""
    response = client.post('/api/v1/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'user' in data['data']


def test_register_duplicate_username(client):
    """测试重复用户名注册"""
    # 先注册一个用户
    client.post('/api/v1/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # 再次使用相同用户名注册
    response = client.post('/api/v1/auth/register', json={
        'username': 'testuser',
        'email': 'test2@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 409


def test_login_success(client, app):
    """测试登录成功"""
    # 先注册用户
    with app.app_context():
        from app.models import User
        from app.extensions import db
        
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    
    # 登录
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'token' in data['data']


def test_login_wrong_password(client, app):
    """测试密码错误"""
    # 先注册用户
    with app.app_context():
        from app.models import User
        from app.extensions import db
        
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    
    # 使用错误密码登录
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 401
