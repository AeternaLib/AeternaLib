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


@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def admin_client(app):
    with app.app_context():
        admin = User(
            name="Admin de prueba",
            document="admin-test",
            email="admin@example.test",
            role="admin",
        )
        admin.set_password("password123")
        admin.save()
        admin_id = admin.id

    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = admin_id
    return client


@pytest.fixture
def reader(app):
    with app.app_context():
        user = User(
            name="Lector de prueba",
            document="reader-test",
            email="reader@example.test",
        )
        user.set_password("password123")
        user.save()
        yield user.id


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("document", ""),
        ("email", ""),
        ("email", "correo-invalido"),
        ("email", "lector@.com"),
        ("email", "lector@example..com"),
        ("email", "lector..prueba@example.com"),
    ],
)
def test_create_rejects_missing_required_fields_and_invalid_email(admin_client, field, value):
    form = {
        "name": "Lector nuevo",
        "document": "reader-new",
        "email": "new@example.test",
        "password": "password123",
    }
    form[field] = value

    response = admin_client.post("/users/new", data=form)

    assert response.status_code == 400


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("document", "reader-test"),
        ("email", "reader@example.test"),
    ],
)
def test_create_rejects_duplicate_document_or_email(admin_client, reader, field, value):
    form = {
        "name": "Lector duplicado",
        "document": "another-reader",
        "email": "another@example.test",
        "password": "password123",
    }
    form[field] = value

    response = admin_client.post("/users/new", data=form)

    assert response.status_code == 400


def test_update_allows_existing_document_and_email_for_same_reader(admin_client, reader):
    response = admin_client.post(
        f"/users/{reader}/edit",
        data={
            "name": "Lector actualizado",
            "document": "reader-test",
            "email": "reader@example.test",
            "password": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Usuario actualizado correctamente" in response.data


def test_delete_rejects_reader_with_active_loan(admin_client, app, reader):
    with app.app_context():
        book = Book(title="Libro de prueba")
        db.session.add(book)
        db.session.flush()
        edition = Edition(
            book_id=book.id,
            isbn_13="9780306406157",
            total_copies=1,
            available_copies=0,
        )
        db.session.add(edition)
        db.session.flush()
        db.session.add(
            Loan(
                edition=edition,
                user_id=reader,
                due_date=date.today() + timedelta(days=7),
            )
        )
        db.session.commit()

    response = admin_client.post(f"/users/{reader}/delete")

    assert response.status_code == 400
    assert "préstamos activos".encode() in response.data


def test_delete_preserves_reader_with_returned_loan_history(admin_client, app, reader):
    with app.app_context():
        book = Book(title="Libro devuelto")
        db.session.add(book)
        db.session.flush()
        edition = Edition(
            book_id=book.id,
            isbn_13="9780306406157",
            total_copies=1,
            available_copies=1,
        )
        db.session.add(edition)
        db.session.flush()
        db.session.add(
            Loan(
                edition=edition,
                user_id=reader,
                due_date=date.today() - timedelta(days=1),
                return_date=date.today(),
            )
        )
        db.session.commit()

    response = admin_client.post(f"/users/{reader}/delete")

    assert response.status_code == 400
    assert "historial de préstamos".encode() in response.data
    with app.app_context():
        assert db.session.get(User, reader) is not None


def test_delete_succeeds_for_reader_without_loans(admin_client, reader):
    response = admin_client.post(f"/users/{reader}/delete")

    assert response.status_code == 302
    with admin_client.application.app_context():
        assert db.session.get(User, reader) is None
