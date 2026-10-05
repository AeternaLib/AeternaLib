from app.extensions import db
from .base import BaseModel

book_authors = db.Table(
    "book_authors",
    db.Column("book_id", db.ForeignKey("book.id"), primary_key=True),
    db.Column("author_id", db.ForeignKey("author.id"), primary_key=True),
)

class Author(BaseModel):
    name = db.Column(db.String(120), nullable=False)
    nationality = db.Column(db.String(60))
    birth_date = db.Column(db.Date)
    biography = db.Column(db.Text)
    bibliography = db.Column(db.Text)
    books = db.relationship("Book", secondary=book_authors, back_populates="authors")