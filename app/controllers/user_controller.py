from flask import Blueprint, render_template

from app.models.user import User
from app.services.access import admin_only

bp = Blueprint("users", __name__, url_prefix="/admin/users")
bp.before_request(admin_only)


@bp.route("/")
def index():
    users = User.query.order_by(User.name).all()
    return render_template("users/index.html", users=users)


@bp.route("/<int:user_id>")
def detail(user_id):
    user = User.get_or_fail(user_id)
    return render_template(
        "users/detail.html",
        user=user,
        active_loans=user.active_loans,
    )
