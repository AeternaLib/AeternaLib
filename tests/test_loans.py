from datetime import date, timedelta

import pytest

from app import create_app
from app.exceptions import (
    BookNotAvailableError,
    LoanAlreadyReturnedError,
    LoanNotFoundError,
    ValidationError,
)
from app.extensions import db
from app.models.book import Book, Edition
from app.models.loan import Loan
from app.models.user import User
from app.services.loan_service import LoanService


class TestConfig:
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOAN_DAYS = 14


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def data(app):
    admin = User(name="Admin de prueba", document="admin-test", email="admin@example.test", role="admin")
    reader = User(name="Lector de prueba", document="reader-test", email="reader@example.test")
    book = Book(title="Cien años de soledad")
    edition = Edition(book=book, isbn_13="9780000000001", total_copies=2, available_copies=2)
    empty = Edition(book=Book(title="Rayuela"), isbn_13="9780000000002", total_copies=1, available_copies=0)
    db.session.add_all([admin, reader, book, edition, empty])
    db.session.commit()
    return {"admin": admin.id, "reader": reader.id, "edition": edition.id, "empty": empty.id}


@pytest.fixture
def admin_client(app, data):
    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = data["admin"]
    return client


# ---- Inventario automático (#9) ----

def test_prestar_descuenta_y_devolver_suma(data):
    edition = db.session.get(Edition, data["edition"])
    loan = LoanService.borrow(data["edition"], data["reader"])
    assert edition.available_copies == 1
    LoanService.return_book(loan.id)
    assert edition.available_copies == 2


def test_inventario_nunca_negativo_ni_mayor_al_total(data):
    edition = db.session.get(Edition, data["edition"])
    loans = [LoanService.borrow(data["edition"], data["reader"]) for _ in range(2)]
    assert edition.available_copies == 0
    with pytest.raises(BookNotAvailableError):
        LoanService.borrow(data["edition"], data["reader"])
    assert edition.available_copies == 0

    edition.available_copies = edition.total_copies  # dato inconsistente a propósito
    db.session.commit()
    LoanService.return_book(loans[0].id)
    assert edition.available_copies == edition.total_copies


# ---- Devoluciones inválidas (#10) ----

def test_devolver_prestamo_inexistente(data, admin_client):
    with pytest.raises(LoanNotFoundError):
        LoanService.return_book(999)
    response = admin_client.post("/loans/999/return")
    assert response.status_code == 404
    assert "no existe" in response.get_data(as_text=True)


def test_devolver_prestamo_ya_devuelto(data, admin_client):
    loan = LoanService.borrow(data["edition"], data["reader"])
    LoanService.return_book(loan.id)
    with pytest.raises(LoanAlreadyReturnedError):
        LoanService.return_book(loan.id)
    response = admin_client.post(f"/loans/{loan.id}/return")
    assert response.status_code == 409
    assert "ya fue devuelto" in response.get_data(as_text=True)


# ---- Pantalla de devolución (#11) ----

def test_devolucion_muestra_dias_de_retraso(data, admin_client):
    loan = LoanService.borrow(data["edition"], data["reader"])
    loan.loan_date = date.today() - timedelta(days=20)
    loan.due_date = date.today() - timedelta(days=3)
    db.session.commit()

    response = admin_client.post(f"/loans/{loan.id}/return", follow_redirects=True)
    assert "3 días de retraso" in response.get_data(as_text=True)
    assert db.session.get(Loan, loan.id).return_date == date.today()


def test_devolucion_a_tiempo(data, admin_client):
    loan = LoanService.borrow(data["edition"], data["reader"])
    response = admin_client.post(f"/loans/{loan.id}/return", follow_redirects=True)
    assert "registrada a tiempo" in response.get_data(as_text=True)


# ---- Bloquear sin ejemplares (#12) ----

def test_prestamo_sin_ejemplares_muestra_error(data, admin_client):
    response = admin_client.post("/loans/new", data={
        "edition_id": data["empty"], "user_id": data["reader"], "days": "14",
    })
    assert response.status_code == 409
    assert "no tiene ejemplares disponibles" in response.get_data(as_text=True)


def test_formulario_deshabilita_libros_sin_ejemplares(data, admin_client):
    html = admin_client.get("/loans/new").get_data(as_text=True)
    option = html.split(f'value="{data["empty"]}"')[1].split(">")[0]
    assert "disabled" in option


# ---- Formulario de préstamo (#8) ----

def test_formulario_registra_y_redirige(data, admin_client):
    response = admin_client.get("/loans/new")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'value="14"' in html
    assert (date.today() + timedelta(days=14)).strftime("%d/%m/%Y") in html

    response = admin_client.post("/loans/new", data={
        "edition_id": data["edition"], "user_id": data["reader"], "days": "7",
    })
    assert response.status_code == 302
    assert response.location.endswith("/loans/")
    loan = Loan.query.one()
    assert loan.due_date == date.today() + timedelta(days=7)

    html = admin_client.get("/loans/").get_data(as_text=True)
    assert "registrado" in html


@pytest.mark.parametrize("days", ["0", "-3", "abc", "61"])
def test_dias_invalidos(data, days):
    with pytest.raises(ValidationError):
        LoanService.borrow(data["edition"], data["reader"], days)


def test_formulario_con_dias_invalidos_no_rompe(data, admin_client):
    response = admin_client.post("/loans/new", data={
        "edition_id": data["edition"], "user_id": data["reader"], "days": "0",
    })
    assert response.status_code == 200
    assert "al menos un día" in response.get_data(as_text=True)
    assert Loan.query.count() == 0


# ---- Activos y atrasados (#13) ----

def test_filtros_activos_atrasados_devueltos(data, admin_client):
    active = LoanService.borrow(data["edition"], data["reader"])
    overdue = LoanService.borrow(data["edition"], data["reader"])
    overdue.due_date = date.today() - timedelta(days=1)
    db.session.commit()

    assert LoanService.list_loans("active") == [active]
    assert LoanService.list_loans("overdue") == [overdue]
    assert LoanService.counts() == {"active": 1, "overdue": 1, "returned": 0, "all": 2}

    LoanService.return_book(active.id)
    assert LoanService.list_loans("returned") == [active]
    assert admin_client.get("/loans/?status=overdue").status_code == 200
    assert admin_client.get("/loans/?status=desconocido").status_code == 200


def test_lector_no_accede_al_formulario(app, data):
    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = data["reader"]
    assert client.get("/loans/new").status_code == 302
