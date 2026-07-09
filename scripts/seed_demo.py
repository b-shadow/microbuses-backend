"""
Seed de demostracion completo para SIG Microbuses.

Crea:
  - 1 Super Admin
  - 1 Admin normal
  - 3 Lineas de microbus
  - 4 Conductores (APPROVED)
  - 4 Buses (uno por linea + extra)
  - 4 Asignaciones bus-conductor activas

Uso:
    # Desde la raiz del proyecto con el venv activado:
    python -m scripts.seed_demo
"""

from datetime import UTC, date, datetime

from sqlalchemy import select

from app.core.dependencies import SessionLocal
from app.core.security import get_password_hash
from app.modules.admins.models import Admin
from app.modules.bus_assignments.models import BusDriverAssignment
from app.modules.buses.models import Bus
from app.modules.drivers.models import Driver
from app.modules.lines.models import Linea


# ── Datos de ejemplo ──────────────────────────────────────────────────────────

ADMINS = [
    {
        'email': 'admin@sig.local',
        'password': 'ChangeMe123!',
        'full_name': 'Super Admin SIG',
        'role': 'SUPER_ADMIN',
    },
    {
        'email': 'coordinador@sig.local',
        'password': 'Coordinador123!',
        'full_name': 'Coordinador Operativo',
        'role': 'ADMIN',
    },
]

LINEAS = [
    {'nombre_linea': 'Línea 1 - Centro',      'color_linea': '#E63946'},
    {'nombre_linea': 'Línea 2 - Norte',       'color_linea': '#2A9D8F'},
    {'nombre_linea': 'Línea 3 - Sur-Oeste',   'color_linea': '#E9C46A'},
]

DRIVERS = [
    {
        'email': 'juan.perez@driver.local',
        'password': 'Driver123!',
        'ci': '1234567',
        'full_name': 'Juan Pérez Mamani',
        'birth_date': date(1985, 3, 15),
        'sex': 'M',
        'phone': '76543210',
        'license_category': 'C',
        'approval_status': 'APPROVED',
    },
    {
        'email': 'maria.quispe@driver.local',
        'password': 'Driver123!',
        'ci': '2345678',
        'full_name': 'María Quispe Flores',
        'birth_date': date(1990, 7, 22),
        'sex': 'F',
        'phone': '71234567',
        'license_category': 'C',
        'approval_status': 'APPROVED',
    },
    {
        'email': 'carlos.rojas@driver.local',
        'password': 'Driver123!',
        'ci': '3456789',
        'full_name': 'Carlos Rojas Condori',
        'birth_date': date(1978, 11, 5),
        'sex': 'M',
        'phone': '79876543',
        'license_category': 'B',
        'approval_status': 'APPROVED',
    },
    {
        'email': 'lucia.vega@driver.local',
        'password': 'Driver123!',
        'ci': '4567890',
        'full_name': 'Lucía Vega Torrez',
        'birth_date': date(1993, 1, 30),
        'sex': 'F',
        'phone': '68001234',
        'license_category': 'C',
        'approval_status': 'PENDING',
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _upsert_admin(db, data: dict) -> Admin:
    existing = db.scalar(select(Admin).where(Admin.email == data['email']))
    if existing:
        existing.role = data['role']
        existing.full_name = data['full_name']
        existing.password_hash = get_password_hash(data['password'])
        existing.is_active = True
        db.add(existing)
        print(f'  [admin] Actualizado: {data["email"]}')
        return existing

    admin = Admin(
        email=data['email'],
        password_hash=get_password_hash(data['password']),
        full_name=data['full_name'],
        role=data['role'],
        is_active=True,
    )
    db.add(admin)
    db.flush()
    print(f'  [admin] Creado: {data["email"]}')
    return admin


def _upsert_linea(db, data: dict) -> Linea:
    existing = db.scalar(select(Linea).where(Linea.nombre_linea == data['nombre_linea']))
    if existing:
        existing.color_linea = data['color_linea']
        existing.is_active = True
        db.add(existing)
        print(f'  [línea] Actualizada: {data["nombre_linea"]}')
        return existing

    linea = Linea(
        nombre_linea=data['nombre_linea'],
        color_linea=data['color_linea'],
        is_active=True,
    )
    db.add(linea)
    db.flush()
    print(f'  [línea] Creada: {data["nombre_linea"]}')
    return linea


def _upsert_driver(db, data: dict) -> Driver:
    existing = db.scalar(select(Driver).where(Driver.email == data['email']))
    if existing:
        existing.full_name = data['full_name']
        existing.approval_status = data['approval_status']
        existing.is_active = True
        db.add(existing)
        print(f'  [conductor] Actualizado: {data["email"]}')
        return existing

    driver = Driver(
        email=data['email'],
        password_hash=get_password_hash(data['password']),
        ci=data['ci'],
        full_name=data['full_name'],
        birth_date=data['birth_date'],
        sex=data['sex'],
        phone=data['phone'],
        license_category=data['license_category'],
        approval_status=data['approval_status'],
        is_active=True,
    )
    db.add(driver)
    db.flush()
    print(f'  [conductor] Creado: {data["email"]}')
    return driver


def _upsert_bus(db, plate: str, model: str, seats: int, internal: str, linea: Linea) -> Bus:
    existing = db.scalar(select(Bus).where(Bus.plate == plate))
    if existing:
        existing.current_line_id = linea.id_linea
        existing.status = 'ACTIVE'
        db.add(existing)
        print(f'  [bus] Actualizado: {plate}')
        return existing

    bus = Bus(
        plate=plate,
        model=model,
        seats_count=seats,
        internal_number=internal,
        current_line_id=linea.id_linea,
        status='ACTIVE',
    )
    db.add(bus)
    db.flush()
    print(f'  [bus] Creado: {plate}')
    return bus


def _assign_bus_driver(db, bus: Bus, driver: Driver) -> None:
    existing = db.scalar(
        select(BusDriverAssignment).where(
            BusDriverAssignment.bus_id == bus.id,
            BusDriverAssignment.is_active.is_(True),
        )
    )
    if existing:
        print(f'  [asignacion] Ya existe: {bus.plate} -> {driver.full_name}')
        return

    assignment = BusDriverAssignment(
        bus_id=bus.id,
        driver_id=driver.id,
        assigned_at=datetime.now(UTC).replace(tzinfo=None),
        is_active=True,
    )
    db.add(assignment)
    print(f'  [asignacion] Creada: {bus.plate} -> {driver.full_name}')


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print('\n========================================')
    print('  SIG Microbuses - Seed de demostracion')
    print('========================================\n')

    with SessionLocal() as db:
        # Admins
        print('[*] Administradores')
        for a in ADMINS:
            _upsert_admin(db, a)

        # Líneas
        print('\n[*] Lineas de microbus')
        lineas = [_upsert_linea(db, l) for l in LINEAS]

        # Conductores
        print('\n[*] Conductores')
        drivers = [_upsert_driver(db, d) for d in DRIVERS]

        # Buses (uno por línea + uno extra en línea 1)
        print('\n[*] Buses')
        buses = [
            _upsert_bus(db, 'ABC-1234', 'Mercedes Sprinter 515', 19, 'INT-001', lineas[0]),
            _upsert_bus(db, 'DEF-5678', 'Toyota Hiace 2022',     15, 'INT-002', lineas[1]),
            _upsert_bus(db, 'GHI-9012', 'Volkswagen Crafter',    22, 'INT-003', lineas[2]),
            _upsert_bus(db, 'JKL-3456', 'Iveco Daily 50C',       20, 'INT-004', lineas[0]),
        ]

        # Asignaciones bus-conductor
        print('\n[*] Asignaciones bus-conductor')
        for bus, driver in zip(buses[:3], drivers[:3]):
            _assign_bus_driver(db, bus, driver)

        db.commit()

    print('\n[OK] Seed completado exitosamente.\n')
    print('Credenciales de acceso:')
    print('  Super Admin -> admin@sig.local          / ChangeMe123!')
    print('  Admin       -> coordinador@sig.local    / Coordinador123!')
    print('  Conductor 1 -> juan.perez@driver.local  / Driver123!')
    print('  Conductor 2 -> maria.quispe@driver.local / Driver123!')
    print()


if __name__ == '__main__':
    main()
