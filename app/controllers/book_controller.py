from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.book import Book, Edition
from app.models.author import Author
from app.exceptions import ValidationError
from app.services.isbn import to_isbn13

bp = Blueprint("books", __name__, url_prefix="/books")

MIN_YEAR = 1  # permite obras antiguas (p. ej. Don Quijote, 1605)


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


def _to_year(raw, label):
    """Año opcional: entero entre MIN_YEAR y el año actual."""
    year = _to_int(raw, label)
    this_year = date.today().year
    if year is not None and not (MIN_YEAR <= year <= this_year):
        raise ValidationError(f"{label} debe estar entre {MIN_YEAR} y {this_year}")
    return year


def _clean_text(field, label, max_len, required=False):
    """Lee un campo de texto, lo recorta y valida obligatoriedad y longitud."""
    value = request.form.get(field, "").strip()
    if not value:
        if required:
            raise ValidationError(f"{label} es obligatorio")
        return None
    if len(value) > max_len:
        raise ValidationError(f"{label} no puede superar los {max_len} caracteres")
    return value


def _read_book_form():
    return {
        "title": _clean_text("title", "El título del libro", 255, required=True),
        "year": _to_year(request.form.get("year"), "El año de publicación"),
        "genre": _clean_text("genre", "El género", 100),
    }


def _read_authors():
    """Autores marcados en el formulario. Si no hay ninguno, devuelve [] (es válido)."""
    ids = [int(raw) for raw in request.form.getlist("authors") if raw.isdigit()]
    if not ids:
        return []
    return Author.query.filter(Author.id.in_(ids)).order_by(Author.name).all()


def _read_edition_form(edition=None):
    raw_isbn = request.form.get("isbn", "").strip()
    if not raw_isbn:
        raise ValidationError("El ISBN es obligatorio")
    isbn_13, isbn_10 = to_isbn13(raw_isbn)  # valida formato y dígito de control

    duplicated = Edition.query.filter_by(isbn_13=isbn_13)
    if edition:
        duplicated = duplicated.filter(Edition.id != edition.id)
    if duplicated.first():
        raise ValidationError(f"Ya existe una edición con el ISBN {isbn_13}")

    year = _to_year(request.form.get("edition_year"), "El año de la edición")

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
        "publisher": _clean_text("publisher", "La editorial", 150),
        "edition_year": year,
        "cover_url": _clean_text("cover_url", "La URL de la portada", 500),
        "price": price,
        "discount_percent": discount,
        "total_copies": total,
    }


def _form_context(book=None):
    return {
        "book": book,
        "loaned": 0,
        "current_year": date.today().year,
        "authors": Author.query.order_by(Author.name).all(),
        "selected_author_ids": [a.id for a in book.authors] if book else [],
    }


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
        authors = _read_authors()
        book = Book(**book_data)
        book.authors = authors
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
        data = _read_book_form()
        authors = _read_authors()  # se valida todo antes de modificar el libro
        for field, value in data.items():
            setattr(book, field, value)
        book.authors = authors  # reemplaza la relación completa
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
        data = _read_edition_form(edition)
        for field, value in data.items():
            setattr(edition, field, value)
        edition.available_copies = edition.total_copies - loaned
        edition.save()
        flash("Edición actualizada correctamente", "success")
        return redirect(url_for("books.detail", book_id=edition.book_id))
    return render_template("books/edition_form.html", book=edition.book, edition=edition,
                           loaned=loaned, current_year=date.today().year)


@bp.route("/editions/<int:edition_id>/delete", methods=["POST"])
def edition_delete(edition_id):
    edition = Edition.get_or_fail(edition_id)
    if edition.loans:
        raise ValidationError("No se puede eliminar una edición que tiene préstamos asociados")
    book_id = edition.book_id
    edition.delete()
    flash("Edición eliminada", "success")
    return redirect(url_for("books.detail", book_id=book_id))