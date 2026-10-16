# Biblioteca Digital — Módulo Historial (RF5 propuesto)

Esta es una implementación **propuesta** de RF5 mientras no se cuente con el enunciado exacto del curso ni el repositorio del equipo.

## Funciones
- Registrar préstamo y devolución confirmados por otro módulo.
- Consultar movimientos por usuario, libro o ambos.
- Persistir registros en SQLite mediante biblioteca estándar de Python.
- Evitar inyección SQL mediante consultas parametrizadas.

## Ejecución
Requiere Python 3.10 o posterior. No requiere paquetes externos.

```bash
python ejemplo_uso.py
python -m unittest discover -s tests -v
```

## Integración con el equipo
Importar `Historial` desde `historial.py` y llamar a `registrar_prestamo` o `registrar_devolucion` **solo cuando el proceso principal haya confirmado exitosamente** la operación. Los identificadores de usuarios, libros y préstamos deben coincidir con los que usa el proyecto real.

**Nota:** Este módulo es un registro de eventos; no valida disponibilidad ni impide devoluciones duplicadas por sí mismo. Para consistencia transaccional con otros módulos SQLite, habrá que compartir la misma conexión/transacción en la integración definitiva.

## Archivos
- `historial.py`: servicio de historial y persistencia SQLite.
- `tests/test_historial.py`: pruebas de registro, consulta, filtros, persistencia y validación.
- `docs/requisitos.md`: RF5 y RNF propuestos.
- `ejemplo_uso.py`: demostración de integración.

## GitHub
Crear una rama propia, incorporar estos archivos en la estructura acordada del proyecto y enviar un Pull Request. No subir el archivo `data/biblioteca.sqlite3`.
