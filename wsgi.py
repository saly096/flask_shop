"""
WSGI 入口文件
用于生产环境部署（Gunicorn/uWSGI/Waitress）

使用方式:
    gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
    或
    waitress-serve --port=5000 wsgi:app
"""
import os
from app import create_app

# 创建应用实例（生产环境配置）
app = create_app('production')

# 确保上传目录存在
upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
os.makedirs(upload_dir, exist_ok=True)
