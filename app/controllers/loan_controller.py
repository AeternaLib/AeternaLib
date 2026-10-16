from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.exceptions import ValidationError
from app.services.access import admin_only, current_user, login_required
from app.services.loan_service import LoanService

bp = Blueprint("loans", __name__, url_prefix="/loans")


@bp.before_request
def protect_admin_routes():
    if request.endpoint in {"loans.index", "loans.new", "loans.return_loan"}:
        return admin_only()


@bp.route("/")
def index():
    status = request.args.get("status")
    if status not in LoanService.STATUSES:
        status = None
    return render_template(
        "loans/index.html",
        loans=LoanService.list_loans(status),
        status=status,
        statuses=LoanService.STATUSES,
        counts=LoanService.counts(),
    )


@bp.route("/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        try:
            loan = LoanService.borrow(
                request.form.get("edition_id", type=int),
                request.form.get("user_id", type=int),
                request.form.get("days"),
            )
        except ValidationError as e:
            flash(e.message, "danger")
        else:
            flash(
                f"Préstamo de «{loan.edition.book.title}» a {loan.user.name} registrado. "
                f"Fecha de devolución: {loan.due_date.strftime('%d/%m/%Y')}.",
                "success",
            )
            return redirect(url_for("loans.index"))

    editions, readers = LoanService.form_options()
    return render_template(
        "loans/new.html",
        editions=editions,
        readers=readers,
        default_days=LoanService.default_days(),
        max_days=LoanService.MAX_DAYS,
        due_date=LoanService.due_date_for(),
        form=request.form,
    )


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
    title = loan.edition.book.title
    if loan.days_late:
        dias = "día" if loan.days_late == 1 else "días"
        flash(f"Devolución de «{title}» registrada con {loan.days_late} {dias} de retraso.", "warning")
    else:
        flash(f"Devolución de «{title}» registrada a tiempo.", "success")
    status = request.form.get("status")
    if status not in LoanService.STATUSES:
        status = None
    return redirect(url_for("loans.index", status=status))
