import re
from functools import wraps
from typing import Callable, Optional, TypeVar

from flask import flash, jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import User

F = TypeVar("F", bound=Callable[..., object])


def is_logged_in() -> bool:
    return session.get("user_id") is not None


def current_user() -> Optional[User]:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, int(user_id))


def is_admin() -> bool:
    user = current_user()
    return bool(user and getattr(user, "is_admin", False))


def require_login(fn: F) -> F:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            if request.blueprint == "api" or request.path.startswith("/api/"):
                from .api_utils import err

                return jsonify(err("Authentication required.", "auth_required")), 401
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def require_admin(fn: F) -> F:
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            if request.blueprint == "api" or request.path.startswith("/api/"):
                from .api_utils import err

                return jsonify(err("Authentication required.", "auth_required")), 401
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        if not is_admin():
            if request.blueprint == "api" or request.path.startswith("/api/"):
                from .api_utils import err

                return jsonify(err("Admin access required.", "forbidden")), 403
            flash("Admin access required.", "danger")
            return redirect(url_for("pages.dashboard"))
        return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def validate_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()))


def validate_password(password: str) -> bool:
    return len(password) >= 8


def create_user(email: str, password: str) -> User:
    normalized = email.strip().lower()
    user = User(
        email=normalized,
        password_hash=generate_password_hash(password),
        is_admin=False,
    )
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email: str, password: str) -> Optional[User]:
    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user:
        return None
    if not check_password_hash(user.password_hash, password):
        return None
    return user
