from app.extensions import db
from .base import BaseModel

class User(BaseModel):
    name = db.Column(db.String(120), nullable=False)
    document = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    loans = db.relationship("Loan", back_populates="user")

    @property
    def active_loans(self):
        return [l for l in self.loans if l.return_date is None]