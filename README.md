# backend

Backend FastAPI del sistema SIG Microbuses.

## Stack
- Python 3.12+
- FastAPI + Uvicorn
- SQLAlchemy 2 + Alembic
- PostgreSQL + PostGIS

## Ejecutar
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_all.py
uvicorn app.main:app --reload
```

Para cargar solo datos mínimos:
```bash
python scripts/seed_line_zero.py
python scripts/seed_admin.py
```

Para importar rutas reales desde Excel (requiere `DatosLineas.xls`):
```bash
python scripts/import_routes_from_excel.py
```

## Variables
Revisar `.env.example` y completar:
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `SUPER_ADMIN_EMAIL`
- `SUPER_ADMIN_PASSWORD`

## Estructura
- `app/core`: configuración y cross-cutting concerns.
- `app/shared`: utilitarios y contratos compartidos.
- `app/modules`: módulos de negocio (arquitectura uniforme).
- `alembic`: migraciones.
- `scripts`: tareas operativas.

## Convención modular
Cada módulo contiene: `router.py`, `schemas.py`, `models.py`, `repository.py`, `service.py`, `validators.py`, `permissions.py`, `events.py`, `mappers.py`, `tests/`.
