"""
商品路由模块
处理商品查询、创建、更新、删除
处理商品分类管理
"""
from flask import Blueprint, request

from app.extensions import db
from app.models import Product, Category
from app.utils import token_required, admin_required, success_response, error_response, paginated_response

products_bp = Blueprint('products', __name__)


@products_bp.route('/', methods=['GET'])
def get_products():
    """获取商品列表"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('q', '')
    is_featured = request.args.get('is_featured', type=bool)
    
    query = Product.query.filter_by(is_active=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    if is_featured is not None:
        query = query.filter_by(is_featured=is_featured)
    
    # 排序
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_by == 'price':
        query = query.order_by(Product.price.desc() if sort_order == 'desc' else Product.price)
    elif sort_by == 'sales':
        query = query.order_by(Product.sales_count.desc() if sort_order == 'desc' else Product.sales_count)
    else:
        query = query.order_by(Product.created_at.desc() if sort_order == 'desc' else Product.created_at)
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return paginated_response(
        items=[p.to_dict() for p in pagination.items],
        total=pagination.total,
        page=page,
        per_page=per_page,
        pages=pagination.pages
    )


@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """获取商品详情"""
    product = Product.query.get_or_404(product_id)
    return success_response({'product': product.to_dict(include_details=True)})


@products_bp.route('/', methods=['POST'])
@token_required
@admin_required
def create_product(current_user):
    """创建商品（管理员）"""
    data = request.get_json()
    
    required_fields = ['name', 'price', 'stock']
    for field in required_fields:
        if field not in data:
            return error_response(f'Missing required field: {field}', 400)
    
    try:
        product = Product(
            name=data['name'],
            description=data.get('description', ''),
            price=data['price'],
            original_price=data.get('original_price'),
            stock=data['stock'],
            main_image=data.get('main_image'),
            images=data.get('images', []),
            category_id=data.get('category_id'),
            is_featured=data.get('is_featured', False),
            weight=data.get('weight'),
            unit=data.get('unit', '件')
        )
        
        db.session.add(product)
        db.session.commit()
        
        return success_response({
            'product': product.to_dict()
        }, 'Product created successfully', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Creation failed: {str(e)}', 500)


@products_bp.route('/<int:product_id>', methods=['PUT'])
@token_required
@admin_required
def update_product(current_user, product_id):
    """更新商品（管理员）"""
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    try:
        updatable_fields = [
            'name', 'description', 'price', 'original_price', 'stock',
            'main_image', 'images', 'category_id', 'is_active',
            'is_featured', 'weight', 'unit'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(product, field, data[field])
        
        db.session.commit()
        
        return success_response({
            'product': product.to_dict()
        }, 'Product updated successfully')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Update failed: {str(e)}', 500)


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_product(current_user, product_id):
    """删除商品（软删除，管理员）"""
    product = Product.query.get_or_404(product_id)
    
    try:
        product.is_active = False
        db.session.commit()
        return success_response(message='Product deleted successfully')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Deletion failed: {str(e)}', 500)


# ==================== 分类管理 ====================

@products_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取分类列表"""
    parent_id = request.args.get('parent_id', type=int)
    
    query = Category.query.filter_by(is_active=True)
    
    if parent_id is not None:
        query = query.filter_by(parent_id=parent_id)
    else:
        query = query.filter_by(parent_id=None)  # 顶级分类
    
    categories = query.order_by(Category.sort_order).all()
    
    return success_response({
        'categories': [c.to_dict(include_children=True) for c in categories]
    })


@products_bp.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """获取分类详情"""
    category = Category.query.get_or_404(category_id)
    return success_response({'category': category.to_dict(include_children=True)})


@products_bp.route('/categories', methods=['POST'])
@token_required
@admin_required
def create_category(current_user):
    """创建分类（管理员）"""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return error_response('Category name is required', 400)
    
    try:
        category = Category(
            name=data['name'],
            description=data.get('description'),
            icon_url=data.get('icon_url'),
            sort_order=data.get('sort_order', 0),
            parent_id=data.get('parent_id')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return success_response({
            'category': category.to_dict()
        }, 'Category created successfully', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Creation failed: {str(e)}', 500)


@products_bp.route('/categories/<int:category_id>', methods=['PUT'])
@token_required
@admin_required
def update_category(current_user, category_id):
    """更新分类（管理员）"""
    category = Category.query.get_or_404(category_id)
    data = request.get_json()
    
    try:
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'icon_url' in data:
            category.icon_url = data['icon_url']
        if 'sort_order' in data:
            category.sort_order = data['sort_order']
        if 'is_active' in data:
            category.is_active = data['is_active']
        
        db.session.commit()
        
        return success_response({
            'category': category.to_dict()
        }, 'Category updated successfully')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Update failed: {str(e)}', 500)
