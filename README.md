# Flask Shop API

一个基于 Flask 的电商后端 API 项目，支持商品管理、订单处理、购物车等功能。

## 项目结构

```
flask_shop/
├── app/                    # 应用主目录
│   ├── __init__.py        # 应用工厂
│   ├── config.py          # 配置文件
│   ├── extensions.py      # Flask 扩展
│   ├── models/            # 数据模型
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── cart.py
│   ├── routes/            # API 路由
│   │   ├── auth.py
│   │   ├── products.py
│   │   ├── orders.py
│   │   └── users.py
│   ├── utils/             # 工具函数
│   └── services/          # 业务逻辑层（预留）
├── migrations/            # 数据库迁移
├── tests/                 # 测试目录
├── static/uploads/        # 文件上传目录
├── requirements.txt       # 依赖
├── run.py                 # 开发启动
├── wsgi.py                # 生产环境入口
└── .env                   # 环境变量
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库等信息
```

### 3. 初始化数据库

```bash
flask init-db
```

### 4. 创建管理员用户

```bash
flask create-admin
```

### 5. 启动应用

```bash
# 开发环境
python run.py

# 或
flask run
```

## API 文档

### 认证模块
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新 Token
- `GET /api/v1/auth/profile` - 获取个人信息
- `PUT /api/v1/auth/profile` - 更新个人信息
- `PUT /api/v1/auth/password` - 修改密码

### 商品模块
- `GET /api/v1/products/` - 商品列表
- `GET /api/v1/products/<id>` - 商品详情
- `POST /api/v1/products/` - 创建商品（管理员）
- `PUT /api/v1/products/<id>` - 更新商品（管理员）
- `DELETE /api/v1/products/<id>` - 删除商品（管理员）
- `GET /api/v1/products/categories` - 分类列表

### 订单模块
- `GET /api/v1/orders/cart` - 购物车
- `POST /api/v1/orders/cart` - 添加购物车
- `PUT /api/v1/orders/cart/<id>` - 更新购物车
- `DELETE /api/v1/orders/cart/<id>` - 删除购物车项
- `POST /api/v1/orders/` - 创建订单
- `GET /api/v1/orders/` - 订单列表
- `GET /api/v1/orders/<id>` - 订单详情
- `POST /api/v1/orders/<id>/cancel` - 取消订单
- `POST /api/v1/orders/<id>/confirm` - 确认收货

### 用户模块（管理员）
- `GET /api/v1/users/` - 用户列表
- `GET /api/v1/users/<id>` - 用户详情
- `PUT /api/v1/users/<id>` - 更新用户
- `DELETE /api/v1/users/<id>` - 删除用户
- `GET /api/v1/users/orders` - 所有订单
- `PUT /api/v1/users/orders/<id>/status` - 更新订单状态

## 部署

### 使用 Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### 使用 Waitress (Windows)

```bash
waitress-serve --port=5000 wsgi:app
```

## 技术栈

- Flask 3.0
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-Migrate
- MySQL/SQLite
- PyMySQL

## 许可证

MIT
