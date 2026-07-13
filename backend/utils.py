from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') not in roles:
                return jsonify(message='You do not have access to this resource.'), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def error(message, status=400):
    return jsonify(message=message), status
