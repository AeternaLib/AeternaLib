from datetime import date, timedelta
from flask import current_app
from app.extensions import db
from app.exceptions import BookNotAvailableError, LoanNotFoundError, LoanAlreadyReturnedError, ValidationError
from app.models.book import Edition
from app.models.user import User
from app.models.loan import Loan


class LoanService:
    @staticmethod
    def borrow(edition_id, user_id, days=None):
        if not edition_id or not user_id:
            raise ValidationError("Edición y usuario son obligatorios")
        edition = Edition.get_or_fail(edition_id)
        user = User.get_or_fail(user_id)
        if edition.available_copies < 1:
            raise BookNotAvailableError(f"'{edition.book.title}' no tiene ejemplares disponibles en esta edición")
        if days is None:
            days = current_app.config["LOAN_DAYS"]
        if days < 1:
            raise ValidationError("La duración del préstamo debe ser de al menos un día")
        loan = Loan(edition=edition, user=user, due_date=date.today() + timedelta(days=days))
        edition.available_copies -= 1
        db.session.add(loan)
        db.session.commit()
        return loan

    @staticmethod
    def return_book(loan_id):
        loan = db.session.get(Loan, loan_id)
        if loan is None:
            raise LoanNotFoundError(f"El préstamo {loan_id} no existe")
        if loan.return_date:
            raise LoanAlreadyReturnedError("Este préstamo ya fue devuelto")
        loan.return_date = date.today()
        loan.edition.available_copies += 1
        db.session.commit()
        return loan

    @staticmethod
    def history(user_id=None, book_id=None, start=None, end=None):
        q = Loan.query
        if user_id:
            q = q.filter_by(user_id=user_id)
        if book_id:
            q = q.join(Loan.edition).filter(Edition.book_id == book_id)
        if start:
            q = q.filter(Loan.loan_date >= start)
        if end:
            q = q.filter(Loan.loan_date <= end)
        return q.order_by(Loan.loan_date.desc()).all()