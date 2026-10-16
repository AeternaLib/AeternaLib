import re
from app.exceptions import ValidationError
from app.models.user import User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[\d\s+()-]+$")


def text(value, label, max_len, required=False):
    value = (value or "").strip()
    if not value:
        if required:
            raise ValidationError(f"{label} es obligatorio")
        return None
    if len(value) > max_len:
        raise ValidationError(f"{label} no puede superar los {max_len} caracteres")
    return value


def validate_contact(form, user=None):
    """Valida nombre, documento, correo y teléfono. `form` es request.form o un dict."""
    name = text(form.get("name"), "El nombre", 120, required=True)
    document = text(form.get("document"), "La identificación", 30, required=True).replace(" ", "")
    email = text(form.get("email"), "El correo", 120, required=True).lower()
    phone = text(form.get("phone"), "El teléfono", 30)

    if not EMAIL_RE.match(email):
        raise ValidationError(f"El correo '{email}' no es válido")

    if phone:
        digits = re.sub(r"\D", "", phone)
        if not PHONE_RE.match(phone) or not (7 <= len(digits) <= 15):
            raise ValidationError("El teléfono debe tener entre 7 y 15 dígitos")

    for field, value, label in (("document", document, "la identificación"),
                                ("email", email, "el correo")):
        duplicated = User.query.filter(getattr(User, field) == value)
        if user:
            duplicated = duplicated.filter(User.id != user.id)
        if duplicated.first():
            raise ValidationError(f"Ya existe un usuario con {label} {value}")

    return {"name": name, "document": document, "email": email, "phone": phone}


def validate_password(password, confirm=None):
    if not password:
        raise ValidationError("La contraseña es obligatoria")
    if len(password) < 8:
        raise ValidationError("La contraseña debe tener al menos 8 caracteres")
    if len(password) > 128:
        raise ValidationError("La contraseña no puede superar los 128 caracteres")
    if confirm is not None and password != confirm:
        raise ValidationError("Las contraseñas no coinciden")