from datetime import date, timedelta
from flask import current_app
from app.extensions import db
from app.exceptions import BookNotAvailableError, LoanNotFoundError, LoanAlreadyReturnedError, ValidationError
from app.models.book import Book, Edition
from app.models.user import User
from app.models.loan import Loan


class LoanService:
    MAX_DAYS = 60
    # Filtros del listado de préstamos: clave -> etiqueta
    STATUSES = {
        "active": "Activos",
        "overdue": "Atrasados",
        "returned": "Devueltos",
    }

    @staticmethod
    def default_days():
        return current_app.config["LOAN_DAYS"]

    @staticmethod
    def parse_days(days):
        """Convierte y valida los días de préstamo (vacío = valor por defecto)."""
        if days is None or str(days).strip() == "":
            return LoanService.default_days()
        try:
            days = int(days)
        except (TypeError, ValueError):
            raise ValidationError("Los días de préstamo deben ser un número entero")
        if days < 1:
            raise ValidationError("La duración del préstamo debe ser de al menos un día")
        if days > LoanService.MAX_DAYS:
            raise ValidationError(f"La duración del préstamo no puede superar {LoanService.MAX_DAYS} días")
        return days

    @staticmethod
    def due_date_for(days=None):
        return date.today() + timedelta(days=LoanService.parse_days(days))

    @staticmethod
    def borrow(edition_id, user_id, days=None):
        if not edition_id or not user_id:
            raise ValidationError("Edición y usuario son obligatorios")
        edition = Edition.get_or_fail(edition_id)
        user = User.get_or_fail(user_id)
        if edition.available_copies < 1:
            raise BookNotAvailableError(f"'{edition.book.title}' no tiene ejemplares disponibles en esta edición")
        days = LoanService.parse_days(days)
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
        edition = loan.edition
        # El inventario nunca supera el total de ejemplares de la edición
        edition.available_copies = min(edition.available_copies + 1, edition.total_copies)
        db.session.commit()
        return loan

    @staticmethod
    def _by_status(status=None):
        today = date.today()
        q = Loan.query
        if status == "active":
            q = q.filter(Loan.return_date.is_(None), Loan.due_date >= today)
        elif status == "overdue":
            q = q.filter(Loan.return_date.is_(None), Loan.due_date < today)
        elif status == "returned":
            q = q.filter(Loan.return_date.isnot(None))
        return q

    @staticmethod
    def list_loans(status=None):
        """Listado de préstamos; status puede ser active, overdue o returned."""
        if status not in LoanService.STATUSES:
            status = None
        q = LoanService._by_status(status)
        return q.order_by(Loan.loan_date.desc(), Loan.id.desc()).all()

    @staticmethod
    def counts():
        counts = {key: LoanService._by_status(key).count() for key in LoanService.STATUSES}
        counts["all"] = Loan.query.count()
        return counts

    @staticmethod
    def form_options():
        """Ediciones y lectores para el formulario de préstamo."""
        editions = Edition.query.join(Book).order_by(Book.title, Edition.edition_year.desc()).all()
        readers = User.query.filter_by(role="client").order_by(User.name).all()
        return editions, readers

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
        return q.order_by(Loan.loan_date.desc(), Loan.id.desc()).all()
