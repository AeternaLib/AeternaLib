from app.extensions import db
from sqlalchemy import func, or_
from app.exceptions import ValidationError
from app.services.text import normalize
from .base import BaseModel
from .author import Author


def _text_filter(query, q, fields):
    """Cada palabra debe aparecer en algún campo (AND entre palabras, OR entre campos)."""
    for term in normalize(q).split():
        like = f"%{term}%"
        query = query.filter(or_(*[func.norm(f).like(like) for f in fields]))
    return query


class Book(BaseModel):  # = la OBRA
    title = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(100))
    year = db.Column(db.Integer)  # año de la obra original
    authors = db.relationship("Author", secondary="book_authors", back_populates="books")
    editions = db.relationship(
        "Edition", backref="book", cascade="all, delete-orphan",
        order_by="Edition.edition_year.desc()",
    )

    @property
    def total_copies(self):
        return sum(e.total_copies for e in self.editions)

    @property
    def available_copies(self):
        return sum(e.available_copies for e in self.editions)

    @property
    def is_available(self):
        return self.available_copies > 0

    @property
    def loans(self):
        return [l for e in self.editions for l in e.loans]

    @property
    def authors_label(self):
        return ", ".join(a.name for a in self.authors) or "Autor desconocido"

    @classmethod
    def genres(cls):
        """Géneros existentes, sin repetir y ordenados, para la lista desplegable."""
        rows = (
            db.session.query(cls.genre)
            .filter(cls.genre.isnot(None), cls.genre != "")
            .distinct()
            .order_by(cls.genre)
            .all()
        )
        return [r[0] for r in rows]

    @classmethod
    def search(cls, q="", genre=None):
        query = cls.query.outerjoin(Edition).outerjoin(cls.authors)
        query = _text_filter(query, q, [
            cls.title, Author.name, Edition.publisher,
            func.replace(Edition.isbn_13, "-", ""),
        ])
        if genre:
            query = query.filter(func.norm(cls.genre) == normalize(genre))
        return query.distinct().order_by(cls.title).all()


class Edition(BaseModel):
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    isbn_13 = db.Column(db.String(13), unique=True, nullable=False)
    isbn_10 = db.Column(db.String(10))
    publisher = db.Column(db.String(150))
    edition_year = db.Column(db.Integer)
    cover_url = db.Column(db.String(500))
    price = db.Column(db.Integer, nullable=False, default=0)             # pesos COP
    discount_percent = db.Column(db.Integer, nullable=False, default=0)  # 0-90
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)
    loans = db.relationship("Loan", backref="edition")

    @property
    def cover_src(self):
        """URL manual si existe; si no, Open Library por ISBN (404 si no la tiene)."""
        if self.cover_url:
            return self.cover_url
        return f"https://covers.openlibrary.org/b/isbn/{self.isbn_13}-L.jpg?default=false"

    @property
    def has_discount(self):
        return self.discount_percent > 0

    @property
    def final_price(self):
        return round(self.price * (100 - self.discount_percent) / 100)

    @property
    def label(self):
        return " · ".join(filter(None, [self.publisher, str(self.edition_year or "")])) or self.isbn_13

    @classmethod
    def catalog_search(cls, q="", genre=None, only_offers=False):
        """Búsqueda para el catálogo público: devuelve ediciones.

        Texto y género se combinan: deben cumplirse los dos.
        """
        query = cls.query.join(Book).outerjoin(Book.authors)
        query = _text_filter(query, q, [
            Book.title, Author.name, cls.publisher,
            func.replace(cls.isbn_13, "-", ""),
        ])
        if genre:
            query = query.filter(func.norm(Book.genre) == normalize(genre))
        if only_offers:
            query = query.filter(cls.discount_percent > 0)
        return query.distinct().order_by(Book.title).all()