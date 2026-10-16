"""RF5 propuesto: historial persistente de préstamos y devoluciones."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Optional

DEFAULT_DB = Path(__file__).resolve().parent / 'data' / 'biblioteca.sqlite3'


@dataclass(frozen=True)
class Movimiento:
    id: int
    usuario_id: str
    libro_id: str
    accion: str
    fecha: str
    prestamo_id: Optional[str]


class Historial:
    """Servicio reutilizable de registro y consulta de movimientos."""

    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = str(db_path)
        if self.db_path != ':memory:':
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._crear_tablas()

    def _conexion(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _crear_tablas(self):
        with self._conexion() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id TEXT NOT NULL,
                libro_id TEXT NOT NULL,
                accion TEXT NOT NULL CHECK (accion IN ('PRESTAMO','DEVOLUCION')),
                fecha TEXT NOT NULL,
                prestamo_id TEXT
            )''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_mov_usuario ON movimientos(usuario_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_mov_libro ON movimientos(libro_id)')

    def registrar(self, usuario_id: str, libro_id: str, accion: str,
                 prestamo_id: Optional[str] = None) -> Movimiento:
        """Registra un evento ya validado por el módulo de préstamos.

        No cambia la disponibilidad del libro ni valida préstamos activos.
        """
        usuario_id = str(usuario_id).strip()
        libro_id = str(libro_id).strip()
        accion = str(accion).strip().upper()
        if not usuario_id or not libro_id:
            raise ValueError('usuario_id y libro_id son obligatorios')
        if accion not in ('PRESTAMO', 'DEVOLUCION'):
            raise ValueError('accion debe ser PRESTAMO o DEVOLUCION')
        fecha = datetime.now(timezone.utc).isoformat(timespec='seconds')
        with self._conexion() as conn:
            cursor = conn.execute(
                'INSERT INTO movimientos (usuario_id, libro_id, accion, fecha, prestamo_id) '
                'VALUES (?, ?, ?, ?, ?)',
                (usuario_id, libro_id, accion, fecha, prestamo_id),
            )
            identificador = cursor.lastrowid
        return Movimiento(identificador, usuario_id, libro_id, accion, fecha, prestamo_id)

    def consultar(self, usuario_id: Optional[str] = None,
                 libro_id: Optional[str] = None) -> list[Movimiento]:
        """Devuelve movimientos del más reciente al más antiguo."""
        filtros = []
        parametros = []
        if usuario_id is not None:
            filtros.append('usuario_id = ?')
            parametros.append(str(usuario_id))
        if libro_id is not None:
            filtros.append('libro_id = ?')
            parametros.append(str(libro_id))
        sql = 'SELECT * FROM movimientos'
        if filtros:
            sql += ' WHERE ' + ' AND '.join(filtros)
        sql += ' ORDER BY id DESC'
        with self._conexion() as conn:
            filas = conn.execute(sql, parametros).fetchall()
        return [Movimiento(**dict(fila)) for fila in filas]

    def registrar_prestamo(self, usuario_id: str, libro_id: str,
                          prestamo_id: Optional[str] = None) -> Movimiento:
        return self.registrar(usuario_id, libro_id, 'PRESTAMO', prestamo_id)

    def registrar_devolucion(self, usuario_id: str, libro_id: str,
                            prestamo_id: Optional[str] = None) -> Movimiento:
        return self.registrar(usuario_id, libro_id, 'DEVOLUCION', prestamo_id)
