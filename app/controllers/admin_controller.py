from datetime import date
from flask import Blueprint, render_template
from app.models.author import Author
from app.models.book import Edition
from app.models import Book, User, Loan
from app.services.access import admin_only

bp = Blueprint("admin", __name__, url_prefix="/admin")
bp.before_request(admin_only)


@bp.route("/")
def dashboard():
    today = date.today()
    active = Loan.query.filter(Loan.return_date.is_(None))
    stats = {
        "books": Book.query.count(),
        "editions": Edition.query.count(),
        "authors": Author.query.count(),
        "users": User.query.count(),
        "active_loans": active.count(),
        "overdue": active.filter(Loan.due_date < today).count(),
    }
    return render_template("admin/dashboard.html", stats=stats)