from app.extensions import db
from sqlalchemy import or_
from app.exceptions import ValidationError
from .base import BaseModel
from .author import Author


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
    def search(cls, q="", genre=None):
        query = cls.query.outerjoin(Edition).outerjoin(cls.authors)
        if q:
            like = f"%{q.strip()}%"
            digits = f"%{q.replace('-', '').strip()}%"
            query = query.filter(or_(
                cls.title.ilike(like), Author.name.ilike(like),
                Edition.publisher.ilike(like), Edition.isbn_13.like(digits),
            ))
        if genre:
            query = query.filter(cls.genre.ilike(f"%{genre.strip()}%"))
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
        """Búsqueda para el catálogo público: devuelve ediciones."""
        query = cls.query.join(Book).outerjoin(Book.authors)
        if q:
            like = f"%{q.strip()}%"
            digits = f"%{q.replace('-', '').strip()}%"
            query = query.filter(or_(
                Book.title.ilike(like), Author.name.ilike(like),
                cls.publisher.ilike(like), cls.isbn_13.like(digits),
            ))
        if genre:
            query = query.filter(Book.genre.ilike(f"%{genre.strip()}%"))
        if only_offers:
            query = query.filter(cls.discount_percent > 0)
        return query.distinct().order_by(Book.title).all()