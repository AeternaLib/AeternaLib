<p align="center">
  <img src="app/static/img/logo.png" alt="AeternaLib" width="180">
</p>

<h1 align="center">AeternaLib</h1>

<p align="center">
  Sistema de gestión de biblioteca digital: catálogo, lectores y préstamos en una sola plataforma web.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-0a365d?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.x-0a365d?logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/SQLite-3-0a365d?logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Bootstrap-5-0a365d?logo=bootstrap&logoColor=white" alt="Bootstrap">
</p>

---

## Descripción

**AeternaLib** es una aplicación web que permite administrar el catálogo de una biblioteca, registrar lectores y controlar el ciclo completo de préstamos y devoluciones. El sistema actualiza el inventario de ejemplares de forma automática, calcula los días de retraso y conserva un historial consultable de todas las operaciones.

## Características

| Módulo | Descripción |
|---|---|
| **Catálogo** | Gestión de libros (título, ISBN, año, género, ejemplares) y autores (datos biográficos y bibliográficos). |
| **Lectores** | Registro de usuarios con sus datos de contacto y préstamos activos. |
| **Préstamos** | Registro de salida, fecha de devolución prevista y devolución efectiva con cálculo de retraso. |
| **Disponibilidad** | Control automático del inventario; impide prestar libros sin ejemplares disponibles. |
| **Historial** | Consulta de préstamos filtrada por usuario, libro o rango de fechas, con indicadores de puntualidad. |
| **Búsqueda** | Localización rápida de libros por título, autor o género. |

## Tecnologías

- **Backend:** Python 3, Flask, Flask-SQLAlchemy
- **Base de datos:** SQLite
- **Frontend:** Jinja2, Bootstrap 5, Bootstrap Icons

## Arquitectura

El proyecto sigue el patrón **MVC** con una capa de servicios que concentra las reglas del dominio.

| Capa | Ubicación | Responsabilidad |
|---|---|---|
| Modelo | `app/models` | Entidades, relaciones y persistencia |
| Vista | `app/templates` | Presentación al usuario |
| Controlador | `app/controllers` | Gestión de rutas y peticiones |
| Servicios | `app/services` | Reglas de negocio (disponibilidad, retrasos) |

Esta separación facilita incorporar nuevas funcionalidades, como multas o reservas, sin modificar el resto del sistema.

```
AeternaLib/
├── app/
│   ├── models/
│   ├── services/
│   ├── controllers/
│   ├── templates/
│   ├── static/
│   ├── config.py
│   ├── extensions.py
│   ├── exceptions.py
│   └── __init__.py
├── instance/
├── tests/
├── requirements.txt
└── run.py
```

## Instalación

**Requisitos:** Python 3.10 o superior.

```powershell
# 1. Clonar el repositorio
git clone <URL-DEL-REPOSITORIO>
cd AeternaLib

# 2. Crear y activar el entorno virtual
py -m venv venv
venv\Scripts\Activate.ps1

# 3. Instalar dependencias
python -m pip install -r requirements.txt

# 4. Ejecutar la aplicación
python run.py
```

La aplicación estará disponible en **http://127.0.0.1:5000**. La base de datos se crea automáticamente en el primer arranque.

## Estado del proyecto

En desarrollo. Actualmente cuenta con la arquitectura base, el modelo de datos, la página principal y el catálogo con búsqueda.

## Autores

- Nahia Sánchez
- Camila Viveros
- Kevin Palma
- Samuel Ospitia

## Licencia

Proyecto académico. Universidad Santiago de Cali.
