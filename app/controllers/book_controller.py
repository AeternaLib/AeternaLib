from flask import Blueprint, render_template, request, redirect, url_for
from app.models.book import Book

bp = Blueprint("books", __name__, url_prefix="/books")

@bp.route("/")
def index():
    books = Book.search(request.args.get("q", ""), request.args.get("genre"))
    return render_template("books/index.html", books=books)