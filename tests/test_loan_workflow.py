from datetime import date, timedelta

import pytest

from app import create_app
from app.extensions import db
from app.models.book import Book, Edition
from app.models.loan import Loan
from app.models.user import User


class TestConfig:
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOAN_DAYS = 14


@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def create_reader(app, document):
    with app.app_context():
        reader = User(
            name="Lector de prueba",
            document=document,
            email=f"{document}@example.test",
        ).save()
        return reader.id


def create_edition(app, available_copies=1):
    with app.app_context():
        book = Book(title="Libro de prueba").save()
        edition = Edition(
            book_id=book.id,
            isbn_13="9780306406157",
            total_copies=1,
            available_copies=available_copies,
        ).save()
        return edition.id


def logged_in_client(app, user_id):
    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = user_id
    return client


def test_reader_can_borrow_from_catalog_and_return_own_loan(app):
    reader_id = create_reader(app, "reader")
    edition_id = create_edition(app)
    client = logged_in_client(app, reader_id)

    detail = client.get(f"/catalog/{edition_id}")
    assert detail.status_code == 200
    assert b"Pedir pr\xc3\xa9stamo" in detail.data

    response = client.post(f"/loans/edition/{edition_id}/borrow")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/account#loans")

    with app.app_context():
        loan = Loan.query.one()
        loan_id = loan.id
        assert loan.user_id == reader_id
        assert loan.edition.available_copies == 0
        assert loan.due_date == date.today() + timedelta(days=14)

    account = client.get("/account")
    assert account.status_code == 200
    assert b"Devolver" in account.data

    response = client.post(f"/loans/{loan_id}/return")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/account#loans")

    with app.app_context():
        loan = db.session.get(Loan, loan_id)
        assert loan.return_date == date.today()
        assert loan.edition.available_copies == 1


def test_reader_cannot_borrow_without_stock(app):
    reader_id = create_reader(app, "reader-no-stock")
    edition_id = create_edition(app, available_copies=0)
    client = logged_in_client(app, reader_id)

    detail = client.get(f"/catalog/{edition_id}")
    assert b"disabled" in detail.data

    response = client.post(f"/loans/edition/{edition_id}/borrow")
    assert response.status_code == 409

    with app.app_context():
        assert Loan.query.count() == 0
        edition = db.session.get(Edition, edition_id)
        assert edition.available_copies == 0


def test_reader_cannot_return_another_readers_loan(app):
    reader_id = create_reader(app, "reader-owner")
    other_reader_id = create_reader(app, "reader-other")
    edition_id = create_edition(app, available_copies=0)
    with app.app_context():
        loan = Loan(
            edition_id=edition_id,
            user_id=reader_id,
            due_date=date.today() + timedelta(days=7),
        ).save()
        loan_id = loan.id

    client = logged_in_client(app, other_reader_id)
    response = client.post(f"/loans/{loan_id}/return")
    assert response.status_code == 403

    with app.app_context():
        loan = db.session.get(Loan, loan_id)
        assert loan.return_date is None
        assert loan.edition.available_copies == 0


def test_returning_overdue_loan_reports_late_days(app):
    reader_id = create_reader(app, "reader-overdue")
    edition_id = create_edition(app, available_copies=0)
    with app.app_context():
        loan = Loan(
            edition_id=edition_id,
            user_id=reader_id,
            due_date=date.today() - timedelta(days=3),
        ).save()
        loan_id = loan.id

    client = logged_in_client(app, reader_id)
    response = client.post(f"/loans/{loan_id}/return", follow_redirects=True)

    assert response.status_code == 200
    assert b"D\xc3\xadas de retraso: 3" in response.data
    with app.app_context():
        loan = db.session.get(Loan, loan_id)
        assert loan.return_date == date.today()
        assert loan.days_late == 3
        assert loan.edition.available_copies == 1
