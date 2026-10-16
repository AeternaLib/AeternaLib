from datetime import date
from app.extensions import db
from .base import BaseModel

class Loan(BaseModel):
    edition_id = db.Column(db.ForeignKey("edition.id"), nullable=False)
    user_id = db.Column(db.ForeignKey("user.id"), nullable=False)
    loan_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    user = db.relationship("User", back_populates="loans")
    # `edition` lo crea automáticamente Edition.loans (backref="edition")

    @property
    def book(self):
        """Mantiene compatible todo lo que usa loan.book (plantillas, servicios)."""
        return self.edition.book

    @property
    def days_late(self):
        end = self.return_date or date.today()
        return max((end - self.due_date).days, 0)

    @property
    def status(self):
        if self.return_date:
            return "Devuelto con retraso" if self.days_late else "Devuelto a tiempo"
        return "Atrasado" if self.days_late else "Activo"