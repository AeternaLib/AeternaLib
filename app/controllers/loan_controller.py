from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models.book import Edition
from app.models.user import User
from app.services.loan_service import LoanService

bp = Blueprint("loans", __name__, url_prefix="/loans")


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


@bp.route("/<int:loan_id>/return", methods=["POST"])
def return_book(loan_id):
    loan = LoanService.return_book(loan_id)
    flash(
        f"Devolución registrada. Días de retraso: {loan.days_late}.",
        "success",
    )
    return redirect(url_for("loans.index"))