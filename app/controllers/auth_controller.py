from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user import User
from app.exceptions import ValidationError
from app.services.access import current_user, login_required
from app.services.user_rules import validate_contact, validate_password

bp = Blueprint("auth", __name__)


def _landing(user):
    return url_for("admin.dashboard") if user.is_admin else url_for("home")


def _safe_next(target):
    """Solo acepta rutas internas, para evitar redirecciones a sitios externos."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return None


def _start_session(user):
    session.clear()
    session["user_id"] = user.id


@bp.route("/login", methods=["GET", "POST"])
def login():
    user = current_user()
    if user:
        return redirect(_landing(user))

    next_url = request.values.get("next", "")
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        found = User.query.filter_by(email=email).first()
        if found and found.check_password(password):
            _start_session(found)
            flash(f"Bienvenido, {found.first_name}", "success")
            return redirect(_safe_next(next_url) or _landing(found))
        flash("Correo o contraseña incorrectos", "danger")
        return render_template("auth/login.html", email=email, next_url=next_url)

    return render_template("auth/login.html", email="", next_url=next_url)


@bp.route("/register", methods=["GET", "POST"])
def register():
    user = current_user()
    if user:
        return redirect(_landing(user))

    if request.method == "POST":
        try:
            data = validate_contact(request.form)
            validate_password(request.form.get("password", ""), request.form.get("confirm", ""))
        except ValidationError as e:
            flash(e.message, "danger")
            return render_template("auth/register.html", form=request.form)

        new_user = User(**data, role="client")  # el registro público siempre crea clientes
        new_user.set_password(request.form["password"])
        new_user.save()
        _start_session(new_user)
        flash("Cuenta creada correctamente. ¡Bienvenido a AeternaLib!", "success")
        return redirect(url_for("home"))

    return render_template("auth/register.html", form={})


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("home"))


@bp.route("/account")
@login_required
def account():
    return render_template("auth/account.html", user=current_user())