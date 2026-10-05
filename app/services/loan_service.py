from datetime import date, timedelta
from flask import current_app
from app.extensions import db
from app.exceptions import BookNotAvailableError, LoanNotFoundError, LoanAlreadyReturnedError, ValidationError
from app.models.book import Book
from app.models.user import User
from app.models.loan import Loan

class LoanService:
    @staticmethod
    def borrow(book_id, user_id, days=None):
        if not book_id or not user_id:
            raise ValidationError("Libro y usuario son obligatorios")
        book = Book.get_or_fail(book_id)
        user = User.get_or_fail(user_id)
        if not book.is_available:
            raise BookNotAvailableError(f"'{book.title}' no tiene ejemplares disponibles")
        days = days or current_app.config["LOAN_DAYS"]
        loan = Loan(book=book, user=user, due_date=date.today() + timedelta(days=days))
        book.available_copies -= 1
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
        loan.book.available_copies += 1
        db.session.commit()
        return loan  # loan.days_late te da los días de retraso

    @staticmethod
    def history(user_id=None, book_id=None, start=None, end=None):
        q = Loan.query
        if user_id: q = q.filter_by(user_id=user_id)
        if book_id: q = q.filter_by(book_id=book_id)
        if start:   q = q.filter(Loan.loan_date >= start)
        if end:     q = q.filter(Loan.loan_date <= end)
        return q.order_by(Loan.loan_date.desc()).all()