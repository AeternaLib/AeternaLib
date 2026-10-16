from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from .base import BaseModel


class User(BaseModel):
    # Para agregar otro tipo de usuario, añade una línea aquí (ej. "librarian": "Bibliotecario")
    ROLE_LABELS = {
        "admin": "Administrador",
        "client": "Cliente",
    }
    DEFAULT_ROLE = "client"

    name = db.Column(db.String(120), nullable=False)
    document = db.Column(db.String(30), unique=True, nullable=False)  # identificación
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30))
    role = db.Column(db.String(20), nullable=False, default="client")
    password_hash = db.Column(db.String(255))
    loans = db.relationship("Loan", back_populates="user")

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return bool(self.password_hash) and check_password_hash(self.password_hash, raw)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def role_label(self):
        return self.ROLE_LABELS.get(self.role, self.role)

    @property
    def first_name(self):
        return (self.name or "").split()[0] if self.name else ""

    @property
    def active_loans(self):
        return [l for l in self.loans if l.return_date is None]

    @classmethod
    def count_admins(cls):
        return cls.query.filter_by(role="admin").count()

    @classmethod
    def search(cls, q="", role=None):
        query = cls.query
        for term in q.split():
            like = f"%{term}%"
            query = query.filter(
                cls.name.ilike(like) | cls.document.ilike(like) | cls.email.ilike(like)
            )
        if role:
            query = query.filter(cls.role == role)
        return query.order_by(cls.name).all()