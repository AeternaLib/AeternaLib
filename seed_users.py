from app import create_app
from app.extensions import db
from app.models.user import User

# Cuentas de prueba para desarrollo
USERS = [
    dict(name="Administrador AeternaLib", document="11111111",
         email="admin@aeternalib.com", phone="3000000001",
         role="admin", password="Admin12345"),
    dict(name="Cliente de Prueba", document="22222222",
         email="cliente@aeternalib.com", phone="3000000002",
         role="client", password="Cliente12345"),
]


def main():
    app = create_app()
    with app.app_context():
        created = 0
        for item in USERS:
            data = dict(item)
            password = data.pop("password")

            exists = User.query.filter(
                (User.email == data["email"]) | (User.document == data["document"])
            ).first()
            if exists:
                continue

            user = User(**data)
            user.set_password(password)
            db.session.add(user)
            created += 1

        db.session.commit()
        print(f"Listo: {created} usuarios nuevos.")
        print("\nCuentas de prueba:")
        for item in USERS:
            print(f"  {item['role']:<7} {item['email']:<24} contraseña: {item['password']}")


if __name__ == "__main__":
    main()