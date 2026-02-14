"""
扩展初始化模块
集中管理所有 Flask 扩展，避免循环导入
"""
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow

# 数据库
db = SQLAlchemy()

# 跨域支持
cors = CORS()

# JWT 认证
jwt = JWTManager()

# 数据库迁移
migrate = Migrate()

# 序列化
ma = Marshmallow()
