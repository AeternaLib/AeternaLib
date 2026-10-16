import json
import random
import re
import time
import urllib.parse
import urllib.request

from app import create_app
from app.extensions import db
from app.models.author import Author
from app.models.book import Book, Edition
from app.services.isbn import to_isbn13
from app.exceptions import ValidationError

HEADERS = {"User-Agent": "AeternaLib/1.0 (proyecto academico)"}
EDITIONS_PER_BOOK = 2
MAX_ISBN_CHECKS = 15

# (título, autor, nacionalidad, género, año de la obra, ISBN preferidos opcionales)
BOOKS = [
    ("Historia universal de la infamia", "Jorge Luis Borges", "Argentina", "Cuento", 1935, ["9788499089492"]),
    ("Ficciones", "Jorge Luis Borges", "Argentina", "Cuento", 1944, []),
    ("El Aleph", "Jorge Luis Borges", "Argentina", "Cuento", 1949, []),
    ("Cien años de soledad", "Gabriel García Márquez", "Colombia", "Novela", 1967, []),
    ("El amor en los tiempos del cólera", "Gabriel García Márquez", "Colombia", "Novela", 1985, []),
    ("Crónica de una muerte anunciada", "Gabriel García Márquez", "Colombia", "Novela", 1981, []),
    ("Rayuela", "Julio Cortázar", "Argentina", "Novela", 1963, []),
    ("Bestiario", "Julio Cortázar", "Argentina", "Cuento", 1951, []),
    ("La casa de los espíritus", "Isabel Allende", "Chile", "Novela", 1982, []),
    ("Eva Luna", "Isabel Allende", "Chile", "Novela", 1987, []),
    ("Pedro Páramo", "Juan Rulfo", "México", "Novela", 1955, []),
    ("El llano en llamas", "Juan Rulfo", "México", "Cuento", 1953, []),
    ("La ciudad y los perros", "Mario Vargas Llosa", "Perú", "Novela", 1963, []),
    ("La fiesta del chivo", "Mario Vargas Llosa", "Perú", "Novela", 2000, []),
    ("Los detectives salvajes", "Roberto Bolaño", "Chile", "Novela", 1998, []),
    ("2666", "Roberto Bolaño", "Chile", "Novela", 2004, []),
    ("El túnel", "Ernesto Sabato", "Argentina", "Novela", 1948, []),
    ("Sobre héroes y tumbas", "Ernesto Sabato", "Argentina", "Novela", 1961, []),
    ("Los pasos perdidos", "Alejo Carpentier", "Cuba", "Novela", 1953, []),
    ("La muerte de Artemio Cruz", "Carlos Fuentes", "México", "Novela", 1962, []),
    ("Veinte poemas de amor y una canción desesperada", "Pablo Neruda", "Chile", "Poesía", 1924, []),
    ("Don Quijote de la Mancha", "Miguel de Cervantes", "España", "Novela", 1605, []),
    ("La sombra del viento", "Carlos Ruiz Zafón", "España", "Novela", 2001, []),
    ("Como agua para chocolate", "Laura Esquivel", "México", "Novela", 1989, []),
]


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def has_cover(isbn):
    url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
    try:
        req = urllib.request.Request(url, method="HEAD", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def edition_info(isbn):
    """Devuelve (editorial, año) de Open Library, o (None, None)."""
    try:
        d = get_json(f"https://openlibrary.org/isbn/{isbn}.json")
        publisher = (d.get("publishers") or [None])[0]
        m = re.search(r"\d{4}", d.get("publish_date", ""))
        return publisher, int(m.group()) if m else None
    except Exception:
        return None, None


def candidate_isbns(title, author, preferred):
    seen = []
    for isbn in preferred:
        if isbn not in seen:
            seen.append(isbn)
    params = urllib.parse.urlencode({
        "title": title, "author": author, "language": "spa",
        "fields": "isbn", "limit": 8,
    })
    try:
        docs = get_json(f"https://openlibrary.org/search.json?{params}").get("docs", [])
    except Exception as exc:
        print(f"   ! Error buscando en Open Library: {exc}")
        docs = []
    for doc in docs:
        for isbn in doc.get("isbn", []):
            if len(isbn) == 13 and isbn.startswith("978") and isbn not in seen:
                seen.append(isbn)
    return seen


def find_editions(title, author, preferred, used):
    found, checks = [], 0
    for isbn in candidate_isbns(title, author, preferred):
        if len(found) >= EDITIONS_PER_BOOK or checks >= MAX_ISBN_CHECKS:
            break
        if isbn in used:
            continue
        try:
            isbn_13, isbn_10 = to_isbn13(isbn)
        except ValidationError:
            continue
        checks += 1
        time.sleep(0.3)
        if has_cover(isbn_13):
            found.append((isbn_13, isbn_10))
            used.add(isbn_13)
    return found


def run():
    db.create_all()
    if Book.query.first():
        print("Ya hay libros cargados; no se hace nada.")
        return

    random.seed(7)
    authors, used = {}, set()
    loaded, skipped = 0, []

    for title, author_name, nationality, genre, year, preferred in BOOKS:
        print(f"Buscando: {title} · {author_name}")
        editions = find_editions(title, author_name, preferred, used)
        if not editions:
            skipped.append(title)
            print("   sin ediciones con portada, se omite")
            continue

        if author_name not in authors:
            authors[author_name] = Author(name=author_name, nationality=nationality)
            authors[author_name].save()

        book = Book(title=title, genre=genre, year=year)
        book.authors.append(authors[author_name])
        book.save()

        for isbn_13, isbn_10 in editions:
            publisher, ed_year = edition_info(isbn_13)
            copies = random.randint(1, 5)
            Edition(
                book_id=book.id, isbn_13=isbn_13, isbn_10=isbn_10,
                publisher=publisher, edition_year=ed_year,
                price=random.randrange(29900, 99900, 1000),
                discount_percent=random.choice([0, 0, 0, 10, 15, 20, 25]),
                total_copies=copies, available_copies=copies,
            ).save()
            print(f"   + {isbn_13}  {publisher or '?'}  ({ed_year or '?'})")
        loaded += 1

    print(f"\nListo: {loaded} libros cargados.")
    if skipped:
        print("Sin portada en Open Library (agrégalos a mano si los quieres):")
        for t in skipped:
            print(f"  - {t}")


if __name__ == "__main__":
    with create_app().app_context():
        run()