from flask import Blueprint, render_template, request
from app.models.book import Book, Edition

bp = Blueprint("catalog", __name__, url_prefix="/catalog")


@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()
    offers = bool(request.args.get("offers"))

    editions = Edition.catalog_search(q, genre, only_offers=offers)

    genres = Book.genres()
    if genre and genre not in genres:  # por si llega un género escrito en la URL
        genres = sorted(genres + [genre])

    return render_template(
        "catalog/index.html",
        editions=editions, genres=genres, q=q, genre=genre, offers=offers,
    )


@bp.route("/<int:edition_id>")
def detail(edition_id):
    edition = Edition.get_or_fail(edition_id)
    others = [e for e in edition.book.editions if e.id != edition.id]
    return render_template("catalog/detail.html", edition=edition, others=others)