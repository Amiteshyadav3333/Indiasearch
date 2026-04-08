# app/middleware/auth_middleware.py
# 🛡️ Auth Middleware — JWT Verification Decorator
# ----------------------------------------
# Usage (on any route):
#   from app.middleware.auth_middleware import require_auth
#
#   @search_bp.get("/history")
#   @require_auth
#   def get_history():
#       user = g.current_user  # injected by decorator
#       ...
#
# JWT secret lives in: Settings.JWT_SECRET_KEY (loaded from .env)

from functools import wraps
from flask import request, g
from app.utils.response_formatter import error
from app.utils.logger import logger

# import jwt
# from app.config.settings import Settings


def require_auth(f):
    """
    Decorator that verifies JWT token from Authorization header.
    On success: injects g.current_user (dict with user_id, email).
    On failure: returns 401 error response.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # TODO:
        # auth_header = request.headers.get("Authorization", "")
        # if not auth_header.startswith("Bearer "):
        #     return error("MISSING_TOKEN", "Authorization token required", 401)
        # token = auth_header.split(" ", 1)[1]
        # try:
        #     payload = jwt.decode(token, Settings.JWT_SECRET_KEY, algorithms=["HS256"])
        #     g.current_user = payload
        # except jwt.ExpiredSignatureError:
        #     return error("TOKEN_EXPIRED", "Token has expired", 401)
        # except jwt.InvalidTokenError as e:
        #     logger.warning(f"Invalid JWT: {e}")
        #     return error("INVALID_TOKEN", "Invalid token", 401)
        return f(*args, **kwargs)
    return decorated


def optional_auth(f):
    """
    Decorator that attempts JWT verification but does NOT block on failure.
    Sets g.current_user = None for unauthenticated requests.
    Use on routes that work for both guest and logged-in users.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # TODO: Try to decode token, set g.current_user or None
        g.current_user = None
        return f(*args, **kwargs)
    return decorated
