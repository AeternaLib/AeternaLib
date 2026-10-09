from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.book import Book, Edition
from app.exceptions import ValidationError
from app.services.isbn import to_isbn13

bp = Blueprint("books", __name__, url_prefix="/books")


def _to_int(raw, label, minimum=0, required=False):
    """Convierte un campo de formulario a entero, validando que sea correcto."""
    raw = (raw or "").strip()
    if not raw:
        if required:
            raise ValidationError(f"{label} es obligatorio")
        return None
    try:
        value = int(raw)
    except ValueError:
        raise ValidationError(f"{label} debe ser un número entero")
    if value < minimum:
        raise ValidationError(f"{label} no puede ser menor que {minimum}")
    return value


def _read_book_form():
    title = request.form.get("title", "").strip()
    if not title:
        raise ValidationError("El título del libro es obligatorio")
    year = _to_int(request.form.get("year"), "El año de publicación")
    if year is not None and year > date.today().year:
        raise ValidationError("El año de publicación no puede ser futuro")
    return {
        "title": title,
        "year": year,
        "genre": request.form.get("genre", "").strip() or None,
    }


def _read_edition_form(edition=None):
    isbn_13, isbn_10 = to_isbn13(request.form.get("isbn", ""))

    duplicated = Edition.query.filter_by(isbn_13=isbn_13)
    if edition:
        duplicated = duplicated.filter(Edition.id != edition.id)
    if duplicated.first():
        raise ValidationError(f"Ya existe una edición con el ISBN {isbn_13}")

    year = _to_int(request.form.get("edition_year"), "El año de la edición")
    if year is not None and year > date.today().year:
        raise ValidationError("El año de la edición no puede ser futuro")

    price = _to_int(request.form.get("price"), "El precio", required=True)
    discount = _to_int(request.form.get("discount_percent"), "El descuento") or 0
    if discount > 90:
        raise ValidationError("El descuento no puede ser mayor a 90%")

    total = _to_int(request.form.get("total_copies"), "El número de ejemplares", required=True)
    if edition:
        loaned = edition.total_copies - edition.available_copies
        if total < loaned:
            raise ValidationError(
                f"No puedes dejar menos de {loaned} ejemplares: hay {loaned} prestados actualmente"
            )

    return {
        "isbn_13": isbn_13,
        "isbn_10": isbn_10,
        "publisher": request.form.get("publisher", "").strip() or None,
        "edition_year": year,
        "cover_url": request.form.get("cover_url", "").strip() or None,
        "price": price,
        "discount_percent": discount,
        "total_copies": total,
    }


def _form_context(book=None):
    return {"book": book, "loaned": 0, "current_year": date.today().year}


# ---------- Libros (obras) ----------

@bp.route("/")
def index():
    books = Book.search(request.args.get("q", ""), request.args.get("genre"))
    return render_template("books/index.html", books=books)


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        book_data = _read_book_form()
        ed_data = _read_edition_form()  # valida todo antes de guardar nada
        book = Book(**book_data)
        book.save()
        Edition(book_id=book.id, **ed_data, available_copies=ed_data["total_copies"]).save()
        flash("Libro creado correctamente", "success")
        return redirect(url_for("books.detail", book_id=book.id))
    return render_template("books/form.html", **_form_context())


@bp.route("/<int:book_id>")
def detail(book_id):
    book = Book.get_or_fail(book_id)
    return render_template("books/detail.html", book=book)


@bp.route("/<int:book_id>/edit", methods=["GET", "POST"])
def edit(book_id):
    book = Book.get_or_fail(book_id)
    if request.method == "POST":
        for field, value in _read_book_form().items():
            setattr(book, field, value)
        book.save()
        flash("Libro actualizado correctamente", "success")
        return redirect(url_for("books.detail", book_id=book.id))
    return render_template("books/form.html", **_form_context(book))


@bp.route("/<int:book_id>/delete", methods=["POST"])
def delete(book_id):
    book = Book.get_or_fail(book_id)
    if book.loans:
        raise ValidationError("No se puede eliminar un libro que tiene préstamos asociados")
    book.delete()
    flash("Libro eliminado", "success")
    return redirect(url_for("books.index"))


# ---------- Ediciones ----------

@bp.route("/<int:book_id>/editions/new", methods=["GET", "POST"])
def edition_create(book_id):
    book = Book.get_or_fail(book_id)
    if request.method == "POST":
        data = _read_edition_form()
        Edition(book_id=book.id, **data, available_copies=data["total_copies"]).save()
        flash("Edición agregada correctamente", "success")
        return redirect(url_for("books.detail", book_id=book.id))
    return render_template("books/edition_form.html", book=book, edition=None,
                           loaned=0, current_year=date.today().year)


@bp.route("/editions/<int:edition_id>/edit", methods=["GET", "POST"])
def edition_edit(edition_id):
    edition = Edition.get_or_fail(edition_id)
    loaned = edition.total_copies - edition.available_copies
    if request.method == "POST":
        for field, value in _read_edition_form(edition).items():
            setattr(edition, field, value)
        edition.available_copies = edition.total_copies - loaned
        edition.save()
        flash("Edición actualizada correctamente", "success")