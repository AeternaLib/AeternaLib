import os
from flask import Flask, render_template, redirect, url_for
from .config import Config
from .extensions import db
from .exceptions import AeternaError
from .services.access import current_user, current_role


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    db.init_app(app)

    # Blueprints (controladores)
    from .controllers.auth_controller import bp as auth_bp
    from .controllers.book_controller import bp as books_bp
    from .controllers.catalog_controller import bp as catalog_bp
    from .controllers.admin_controller import bp as admin_bp
    from .controllers.author_controller import bp as authors_bp
    from .controllers.loan_controller import bp as loans_bp
    from .controllers.user_controller import bp as users_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(authors_bp)
    app.register_blueprint(loans_bp)
    app.register_blueprint(users_bp)

    # Usuario y rol disponibles en todas las plantillas
    @app.context_processor
    def inject_auth_state():
        user = current_user()
        return {
            "current_user": user,
            "role": current_role(),
            "is_admin": bool(user and user.is_admin),
            "is_logged_in": user is not None,
        }

    # Página principal (pública). El administrador va directo a su panel.
    @app.route("/")
    def home():
        if current_role() == "admin":
            return redirect(url_for("admin.dashboard"))
        return render_template("home.html")

    # Manejo de errores del dominio
    @app.errorhandler(AeternaError)
    def handle_domain_error(e):
        return render_template("error.html", message=e.message), e.status_code

    @app.errorhandler(404)
    def handle_not_found(e):
        return render_template("error.html", message="La página que buscas no existe"), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return render_template("error.html", message="Esa acción no está permitida desde el navegador"), 405

    # Crear tablas
    with app.app_context():
        from . import models  # noqa
        db.create_all()

    return app