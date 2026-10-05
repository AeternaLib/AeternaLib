from app.extensions import db
from app.exceptions import ValidationError
from .base import BaseModel
from .author import book_authors

class Book(BaseModel):
    title = db.Column(db.String(200), nullable=False, index=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    year = db.Column(db.Integer)
    genre = db.Column(db.String(80), index=True)
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)
    authors = db.relationship("Author", secondary=book_authors, back_populates="books")
    loans = db.relationship("Loan", back_populates="book")

    @property
    def is_available(self):
        return self.available_copies > 0

    @classmethod
    def search(cls, q="", genre=None):
        from .author import Author
        query = cls.query.outerjoin(cls.authors)
        if q:
            like = f"%{q}%"
            query = query.filter(db.or_(cls.title.ilike(like), Author.name.ilike(like)))
        if genre:
            query = query.filter(cls.genre == genre)
        return query.distinct().all()