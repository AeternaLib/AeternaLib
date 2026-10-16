from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models.loan import Loan
from app.services.access import admin_only, current_user, login_required
from app.services.loan_service import LoanService

bp = Blueprint("loans", __name__, url_prefix="/loans")


@bp.before_request
def protect_admin_routes():
    if request.endpoint in {"loans.index", "loans.return_loan"}:
        return admin_only()


@bp.route("/")
def index():
    loans = Loan.query.order_by(Loan.loan_date.desc(), Loan.id.desc()).all()
    return render_template("loans/index.html", loans=loans)


@bp.route("/editions/<int:edition_id>/borrow", methods=["POST"])
@login_required
def borrow(edition_id):
    loan = LoanService.borrow(edition_id, current_user().id)
    flash(
        f"Préstamo de «{loan.edition.book.title}» registrado. "
        f"Fecha de devolución: {loan.due_date.strftime('%d/%m/%Y')}.",
        "success",
    )
    return redirect(url_for("catalog.detail", edition_id=edition_id))


@bp.route("/<int:loan_id>/return", methods=["POST"])
def return_loan(loan_id):
    loan = LoanService.return_book(loan_id)
    flash(f"Devolución de «{loan.edition.book.title}» registrada correctamente.", "success")
    return redirect(url_for("loans.index"))
