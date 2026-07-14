from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash


def role_required(*roles):
    # Route decorator: requires a valid JWT, one of the given role claims, and an active account, checked fresh on every request (not just at login).
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') not in roles:
                return jsonify(message='You do not have access to this resource.'), 403
            if not current_user_is_active():
                return jsonify(message='Your account has been deactivated. Please contact the institute admin.'), 401
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def current_user_is_active():
    # Looks up the current JWT's user row and returns its is_active flag.
    from models import User
    user = User.query.get(int(get_jwt_identity()))
    return user is not None and user.is_active


def error(message, status=400):
    # Shorthand for a JSON error response; also logs to the backend terminal
    # so request failures (e.g. failed logins) are visible without a debugger.
    current_app.logger.warning('[%s] %s', status, message)
    return jsonify(message=message), status


def apply_password_change(user, data):
    """Applies an optional password change from a profile-update payload onto `user`.

    No-op (returns None) if `new_password` is absent/blank, so callers can update other
    profile fields without touching the password. Returns a Flask error response if the
    requested change is invalid.
    """
    new_password = (data.get('new_password') or '').strip()
    # No password fields submitted; nothing to change.
    if not new_password:
        return None
    current_password = (data.get('current_password') or '').strip()
    # Current password must be supplied and match the stored hash.
    if not current_password or not check_password_hash(user.password, current_password):
        return error('Current password is incorrect.')
    if len(new_password) < 6:
        return error('New password must be at least 6 characters long.')
    # Rejects setting the password to its current value.
    if check_password_hash(user.password, new_password):
        return error('New password must be different from your current password.')
    user.password = generate_password_hash(new_password)
    return None
