from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models.book import Edition
from app.models.loan import Loan
from app.models.user import User
from app.services.access import admin_only, current_user, login_required
from app.services.loan_service import LoanService

bp = Blueprint("loans", __name__, url_prefix="/loans")


@bp.before_request
def restrict_admin_routes():
    if request.endpoint in {"loans.index", "loans.create"}:
        return admin_only()


@bp.route("/")
def index():
    loans = LoanService.history()
    return render_template("loans/index.html", loans=loans)


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        LoanService.borrow(
            edition_id=request.form.get("edition_id", type=int),
            user_id=request.form.get("user_id", type=int),
        )
        flash("Préstamo registrado correctamente", "success")
        return redirect(url_for("loans.index"))

    editions = Edition.query.order_by(Edition.book_id, Edition.edition_year.desc()).all()
    users = User.query.order_by(User.name).all()
    return render_template("loans/form.html", editions=editions, users=users)


@bp.route("/edition/<int:edition_id>/borrow", methods=["POST"])
@login_required
def borrow(edition_id):
    user = current_user()
    LoanService.borrow(edition_id=edition_id, user_id=user.id)
    flash("Préstamo registrado correctamente", "success")
    return redirect(url_for("auth.account", _anchor="loans"))


@bp.route("/<int:loan_id>/return", methods=["POST"])
@login_required
def return_loan(loan_id):
    user = current_user()
    loan = LoanService.return_book(
        loan_id,
        user_id=None if user.is_admin else user.id,
    )
    flash(
        f"Devolución registrada. Días de retraso: {loan.days_late}.",
        "success",
    )
    destination = "loans.index" if user.is_admin else "auth.account"
    return redirect(url_for(destination, _anchor=None if user.is_admin else "loans"))