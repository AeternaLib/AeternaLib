import re
from app.exceptions import ValidationError


def clean(raw):
    return re.sub(r"[\s-]", "", raw or "").upper()


def _valid_10(s):
    if not re.fullmatch(r"\d{9}[\dX]", s):
        return False
    total = sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(s))
    return total % 11 == 0


def _valid_13(s):
    if not re.fullmatch(r"\d{13}", s):
        return False
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(s[:12]))
    return (10 - total % 10) % 10 == int(s[12])


def _check_13(first12):
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(first12))
    return str((10 - total % 10) % 10)


def to_isbn13(raw):
    """Devuelve (isbn13, isbn10 o None). Lanza ValidationError si no es válido."""
    s = clean(raw)
    if len(s) == 10 and _valid_10(s):
        base = "978" + s[:9]
        return base + _check_13(base), s
    if len(s) == 13 and _valid_13(s):
        return s, to_isbn10(s)
    raise ValidationError(f"El ISBN '{raw}' no es válido (revisa el dígito de control)")


def to_isbn10(isbn13):
    if not isbn13.startswith("978"):
        return None  # los 979 no tienen equivalente ISBN-10
    body = isbn13[3:12]
    total = sum((10 - i) * int(c) for i, c in enumerate(body))
    check = (11 - total % 11) % 11
    return body + ("X" if check == 10 else str(check))