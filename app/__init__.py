import os
from datetime import date
from flask import Flask, render_template
from .config import Config
from .extensions import db
from .exceptions import AeternaError


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    db.init_app(app)

    # Blueprints (controladores)
    from .controllers.book_controller import bp as books_bp
    app.register_blueprint(books_bp)

    # Activa estos cuando cada controlador defina su `bp`:
    # from .controllers.author_controller import bp as authors_bp
    # from .controllers.user_controller import bp as users_bp
    # from .controllers.loan_controller import bp as loans_bp
    # app.register_blueprint(authors_bp)
    # app.register_blueprint(users_bp)
    # app.register_blueprint(loans_bp)

    # Página principal
    @app.route("/")
    def home():
        from .models import Book, User, Loan
        stats = {
            "books": Book.query.count(),
            "users": User.query.count(),
            "active_loans": Loan.query.filter(Loan.return_date.is_(None)).count(),
            "overdue": Loan.query.filter(
                Loan.return_date.is_(None), Loan.due_date < date.today()
            ).count(),
        }
        return render_template("home.html", stats=stats)

    # Manejo de errores del dominio
    @app.errorhandler(AeternaError)
    def handle_domain_error(e):
        return render_template("error.html", message=e.message), e.status_code

    # Crear tablas
    with app.app_context():
        from . import models  # noqa
        db.create_all()

    return app