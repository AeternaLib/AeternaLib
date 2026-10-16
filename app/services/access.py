from flask import session, redirect, url_for, flash

ROLES = ("guest", "reader", "admin")


def current_role():
    """TEMPORAL: sale de la sesión. Con login real, devuelve el rol del usuario."""
    return session.get("role", "guest")


def admin_only():
    """Úsalo con bp.before_request: si no es admin, lo manda al inicio."""
    if current_role() != "admin":
        flash("No tienes permiso para acceder a esa sección", "danger")
        return redirect(url_for("home"))