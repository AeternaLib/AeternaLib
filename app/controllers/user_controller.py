from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.user import User
from app.exceptions import ValidationError
from app.services.access import admin_only, current_user
from app.services.user_rules import validate_contact, validate_password

bp = Blueprint("users", __name__, url_prefix="/users")
bp.before_request(admin_only)  # solo el administrador gestiona usuarios


def _read_form(user=None):
    """Lee y valida el formulario. Si se pasa `user`, es una edición."""
    data = validate_contact(request.form, user)
    role = request.form.get("role", User.DEFAULT_ROLE).strip()

    if role not in User.ROLE_LABELS:
        raise ValidationError(f"El tipo de usuario '{role}' no es válido")

    # Siempre debe quedar al menos un administrador
    if user and user.is_admin and role != "admin" and User.count_admins() <= 1:
        raise ValidationError("No puedes quitar el rol al único administrador")

    data["role"] = role
    return data


def _form_context(user=None):
    return {"user": user, "roles": User.ROLE_LABELS}


@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    role = request.args.get("role", "").strip()
    return render_template(
        "users/index.html",
        users=User.search(q, role or None), q=q, role=role, roles=User.ROLE_LABELS,
    )


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        data = _read_form()
        password = request.form.get("password", "")
        validate_password(password)
        user = User(**data)
        user.set_password(password)
        user.save()
        flash("Usuario creado correctamente", "success")
        return redirect(url_for("users.detail", user_id=user.id))
    return render_template("users/form.html", **_form_context())


@bp.route("/<int:user_id>")
def detail(user_id):
    user = User.get_or_fail(user_id)
    return render_template("users/detail.html", user=user)


@bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
def edit(user_id):
    user = User.get_or_fail(user_id)
    if request.method == "POST":
        data = _read_form(user)
        password = request.form.get("password", "")
        if password:  # en edición, la contraseña es opcional
            validate_password(password)
        for field, value in data.items():
            setattr(user, field, value)
        if password:
            user.set_password(password)
        user.save()
        flash("Usuario actualizado correctamente", "success")
        return redirect(url_for("users.detail", user_id=user.id))
    return render_template("users/form.html", **_form_context(user))


@bp.route("/<int:user_id>/delete", methods=["POST"])
def delete(user_id):
    user = User.get_or_fail(user_id)
    if user.id == current_user().id:
        raise ValidationError("No puedes eliminar tu propia cuenta")
    if user.active_loans:
        raise ValidationError("No se puede eliminar un usuario con préstamos activos")
    if user.loans:
        raise ValidationError("No se puede eliminar un usuario con historial de préstamos")
    if user.is_admin and User.count_admins() <= 1:
        raise ValidationError("No puedes eliminar al único administrador")
    user.delete()
    flash("Usuario eliminado", "success")
    return redirect(url_for("users.index"))