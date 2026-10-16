from flask import Blueprint, render_template
from app.models.author import Author
from app.models.book import Edition
from app.models import Book, User
from app.services.access import admin_only
from app.services.loan_service import LoanService

bp = Blueprint("admin", __name__, url_prefix="/admin")
bp.before_request(admin_only)


@bp.route("/")
def dashboard():
    loans = LoanService.counts()
    stats = {
        "books": Book.query.count(),
        "editions": Edition.query.count(),
        "authors": Author.query.count(),
        "users": User.query.count(),
        "active_loans": loans["active"],
        "overdue": loans["overdue"],
    }
    return render_template("admin/dashboard.html", stats=stats)