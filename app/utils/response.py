"""响应工具函数"""
from flask import jsonify


def success_response(data=None, message='Success', code=200):
    """成功响应"""
    response = {
        'success': True,
        'message': message,
        'code': code
    }
    if data is not None:
        response['data'] = data
    return jsonify(response), code


def error_response(message='Error', code=400, errors=None):
    """错误响应"""
    response = {
        'success': False,
        'message': message,
        'code': code
    }
    if errors:
        response['errors'] = errors
    return jsonify(response), code


def paginated_response(items, total, page, per_page, pages):
    """分页响应"""
    return jsonify({
        'success': True,
        'data': {
            'items': items,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': pages
            }
        }
    })
