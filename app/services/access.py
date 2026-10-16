from functools import wraps
from flask import session, redirect, url_for, flash, request, g
from app.extensions import db


def current_user():
    """Usuario de la sesión, o None si es visitante."""
    if "user" not in g:
        from app.models.user import User
        uid = session.get("user_id")
        g.user = db.session.get(User, uid) if uid else None
    return g.user


def current_role():
    user = current_user()
    return user.role if user else "guest"


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Inicia sesión para continuar", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_only():
    """Úsalo con bp.before_request: solo deja pasar a administradores."""
    user = current_user()
    if not user:
        flash("Inicia sesión para continuar", "warning")
        return redirect(url_for("auth.login", next=request.path))
    if not user.is_admin:
        flash("No tienes permiso para acceder a esa sección", "danger")
        return redirect(url_for("home"))