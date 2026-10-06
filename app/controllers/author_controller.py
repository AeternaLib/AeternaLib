from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.author import Author
from app.exceptions import ValidationError

bp = Blueprint("authors", __name__, url_prefix="/authors")


def _read_form():
    """Lee y valida el formulario de autor. Lanza ValidationError si hay datos inválidos."""
    name = request.form.get("name", "").strip()
    if not name:
        raise ValidationError("El nombre del autor es obligatorio")

    birth_date = None
    birth_raw = request.form.get("birth_date", "").strip()
    if birth_raw:
        try:
            birth_date = date.fromisoformat(birth_raw)
        except ValueError:
            raise ValidationError("La fecha de nacimiento no es válida")
        if birth_date > date.today():
            raise ValidationError("La fecha de nacimiento no puede ser futura")

    return {
        "name": name,
        "nationality": request.form.get("nationality", "").strip() or None,
        "birth_date": birth_date,
        "biography": request.form.get("biography", "").strip() or None,
        "bibliography": request.form.get("bibliography", "").strip() or None,
    }


@bp.route("/")
def index():
    authors = Author.query.order_by(Author.name).all()
    return render_template("authors/index.html", authors=authors)


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        Author(**_read_form()).save()
        flash("Autor creado correctamente", "success")
        return redirect(url_for("authors.index"))
    return render_template("authors/form.html", author=None, today=date.today().isoformat())


@bp.route("/<int:author_id>")
def detail(author_id):
    author = Author.get_or_fail(author_id)
    return render_template("authors/detail.html", author=author)


@bp.route("/<int:author_id>/edit", methods=["GET", "POST"])
def edit(author_id):
    author = Author.get_or_fail(author_id)
    if request.method == "POST":
        for field, value in _read_form().items():
            setattr(author, field, value)
        author.save()
        flash("Autor actualizado correctamente", "success")
        return redirect(url_for("authors.detail", author_id=author.id))
    return render_template("authors/form.html", author=author, today=date.today().isoformat())


@bp.route("/<int:author_id>/delete", methods=["POST"])
def delete(author_id):
    author = Author.get_or_fail(author_id)
    author.delete()
    flash("Autor eliminado", "success")
    return redirect(url_for("authors.index"))