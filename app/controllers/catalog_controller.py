from flask import Blueprint, render_template, request
from app.models.book import Edition

bp = Blueprint("catalog", __name__, url_prefix="/catalog")


@bp.route("/")
def index():
    editions = Edition.catalog_search(
        request.args.get("q", ""),
        request.args.get("genre"),
        only_offers=bool(request.args.get("offers")),
    )
    return render_template("catalog/index.html", editions=editions)


@bp.route("/<int:edition_id>")
def detail(edition_id):
    edition = Edition.get_or_fail(edition_id)
    others = [e for e in edition.book.editions if e.id != edition.id]
    return render_template("catalog/detail.html", edition=edition, others=others)