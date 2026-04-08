# app/routes/auth_routes.py
# 🔐 Auth Routes — Thin Controller
# ----------------------------------------
# Endpoints:
#   POST /api/auth/register     → Register new user
#   POST /api/auth/login        → Login + issue JWT
#   POST /api/auth/logout       → Invalidate session
#   POST /api/auth/send-otp     → Send OTP (email/mobile)
#   POST /api/auth/verify-otp   → Verify OTP
#   GET  /api/auth/me           → Get current user profile
#
# All business logic lives in: app/services/auth_service.py  (TODO: create)
# Auth guard lives in:         app/middleware/auth_middleware.py

from flask import Blueprint, request
from app.utils.response_formatter import success, error

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    """Register a new user."""
    # TODO: data = request.get_json()
    # TODO: result = AuthService.register(data)
    # TODO: return success(result)
    return success({"message": "register stub"})


@auth_bp.post("/login")
def login():
    """Login and return JWT token."""
    # TODO: data = request.get_json()
    # TODO: token = AuthService.login(data)
    # TODO: return success({"token": token})
    return success({"message": "login stub"})


@auth_bp.post("/logout")
def logout():
    """Logout and invalidate token."""
    # TODO: AuthService.logout(request)
    return success({"message": "logout stub"})


@auth_bp.post("/send-otp")
def send_otp():
    """Send OTP to email or mobile."""
    # TODO: data = request.get_json()
    # TODO: AuthService.send_otp(data["contact"], data["type"])
    return success({"message": "OTP sent stub"})


@auth_bp.post("/verify-otp")
def verify_otp():
    """Verify OTP and return token."""
    # TODO: data = request.get_json()
    # TODO: token = AuthService.verify_otp(data)
    return success({"message": "OTP verified stub"})


@auth_bp.get("/me")
def me():
    """Return current authenticated user info."""
    # TODO: Apply auth_middleware decorator
    # TODO: user = AuthService.get_current_user(request)
    return success({"message": "current user stub"})
