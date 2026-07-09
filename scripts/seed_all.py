"""Seed demo data for all active application tables.

Run after migrations:
    python scripts/seed_all.py

Idempotent: safe to run multiple times; records are upserted by unique keys.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.dependencies import SessionLocal
from app.core.security import get_password_hash
from app.core.settings import get_settings
from app.modules.active_trips.models import ActiveTrip
from app.modules.admins.models import Admin
from app.modules.audit.models import AuditLog
from app.modules.bus_assignments.models import BusDriverAssignment
from app.modules.buses.models import Bus
from app.modules.drivers.models import Driver
from app.modules.favorites.models import FavoritePlace
from app.modules.file_imports.models import FileImport
from app.modules.lines.models import Linea
from app.modules.offline_packages.models import OfflinePackage
from app.modules.puntos_trasbordos.models import PuntoTrasbordo
from app.modules.route_points.models import LineaPunto
from app.modules.routes.models import LineaRuta
from app.modules.settings.models import Setting
from app.modules.stops.models import Punto
from app.modules.tracking.models import TrackingLocation
from app.modules.user_history.models import UserRouteHistory
from app.modules.users.models import User

# Santa Cruz de la Sierra reference coordinates
PLAZA_24 = (-63.1821, -17.7833)
AV_BUSCH = (-63.1750, -17.7900)
EQUIPETROL = (-63.1680, -17.7650)
PLAN_3000 = (-63.2100, -17.8200)

DEMO_PASSWORD = 'Demo1234!'


def _point(lng: float, lat: float) -> str:
    return f'SRID=4326;POINT({lng} {lat})'


def _upsert_linea(db, nombre: str, color: str, *, is_active: bool = True) -> Linea:
    row = db.scalar(select(Linea).where(Linea.nombre_linea == nombre))
    if row:
        row.color_linea = color
        row.is_active = is_active
        db.add(row)
        db.flush()
        return row

    row = Linea(nombre_linea=nombre, color_linea=color, is_active=is_active)
    db.add(row)
    db.flush()
    return row


def _upsert_punto(db, lat: float, lng: float, descripcion: str, stop: str = 'S') -> Punto:
    row = db.scalar(
        select(Punto).where(
            Punto.latitud == Decimal(str(lat)),
            Punto.longitud == Decimal(str(lng)),
            Punto.descripcion == descripcion,
        )
    )
    if row:
        row.stop = stop
        row.is_active = True
        db.add(row)
        db.flush()
        return row

    row = Punto(
        latitud=Decimal(str(lat)),
        longitud=Decimal(str(lng)),
        descripcion=descripcion,
        stop=stop,
        is_active=True,
    )
    db.add(row)
    db.flush()
    return row


def seed_transport(db) -> dict:
    linea_0 = _upsert_linea(db, '0', '#64748B')
    linea_100 = _upsert_linea(db, '100', '#EF4444')
    linea_101 = _upsert_linea(db, '101', '#3B82F6')

    p_plaza = _upsert_punto(db, PLAZA_24[1], PLAZA_24[0], 'Plaza 24 de Septiembre')
    p_busch = _upsert_punto(db, AV_BUSCH[1], AV_BUSCH[0], 'Av. Busch')
    p_equip = _upsert_punto(db, EQUIPETROL[1], EQUIPETROL[0], 'Equipetrol')
    p_plan = _upsert_punto(db, PLAN_3000[1], PLAN_3000[0], 'Plan 3000')

    ruta_100 = db.scalar(
        select(LineaRuta).where(LineaRuta.id_linea == linea_100.id_linea, LineaRuta.id_ruta == 1)
    )
    if not ruta_100:
        ruta_100 = LineaRuta(
            id_linea=linea_100.id_linea,
            id_ruta=1,
            descripcion='Plaza 24 → Plan 3000 (Ida)',
            distancia=Decimal('12.50'),
            tiempo=Decimal('35.00'),
            is_active=True,
        )
        db.add(ruta_100)
        db.flush()

    ruta_101 = db.scalar(
        select(LineaRuta).where(LineaRuta.id_linea == linea_101.id_linea, LineaRuta.id_ruta == 1)
    )
    if not ruta_101:
        ruta_101 = LineaRuta(
            id_linea=linea_101.id_linea,
            id_ruta=1,
            descripcion='Equipetrol → Av. Busch (Ida)',
            distancia=Decimal('6.20'),
            tiempo=Decimal('18.00'),
            is_active=True,
        )
        db.add(ruta_101)
        db.flush()

    route_points_100 = [
        (p_plaza.id_punto, p_busch.id_punto, 1),
        (p_busch.id_punto, p_plan.id_punto, 2),
    ]
    for id_punto, id_punto_dest, orden in route_points_100:
        exists = db.scalar(
            select(LineaPunto).where(
                LineaPunto.id_linea_ruta == ruta_100.id_linea_ruta,
                LineaPunto.orden == orden,
            )
        )
        if not exists:
            db.add(
                LineaPunto(
                    id_linea_ruta=ruta_100.id_linea_ruta,
                    id_punto=id_punto,
                    id_punto_dest=id_punto_dest,
                    orden=orden,
                    distancia=Decimal('6.00'),
                    tiempo=Decimal('15.00'),
                )
            )

    route_points_101 = [
        (p_equip.id_punto, p_busch.id_punto, 1),
    ]
    for id_punto, id_punto_dest, orden in route_points_101:
        exists = db.scalar(
            select(LineaPunto).where(
                LineaPunto.id_linea_ruta == ruta_101.id_linea_ruta,
                LineaPunto.orden == orden,
            )
        )
        if not exists:
            db.add(
                LineaPunto(
                    id_linea_ruta=ruta_101.id_linea_ruta,
                    id_punto=id_punto,
                    id_punto_dest=id_punto_dest,
                    orden=orden,
                    distancia=Decimal('6.20'),
                    tiempo=Decimal('18.00'),
                )
            )

    trasbordo = db.scalar(
        select(PuntoTrasbordo).where(
            PuntoTrasbordo.id_punto == p_busch.id_punto,
            PuntoTrasbordo.id_linea_origen == linea_100.id_linea,
            PuntoTrasbordo.id_linea_destino == linea_101.id_linea,
        )
    )
    if not trasbordo:
        db.add(
            PuntoTrasbordo(
                id_punto=p_busch.id_punto,
                id_linea_origen=linea_100.id_linea,
                id_linea_destino=linea_101.id_linea,
                penalizacion_min=5,
            )
        )

    db.flush()
    print('[seed_all] Transport: lineas, puntos, rutas, trasbordos')
    return {
        'linea_100': linea_100,
        'linea_101': linea_101,
        'ruta_100': ruta_100,
        'p_plaza': p_plaza,
        'p_equip': p_equip,
    }


def seed_admins(db) -> Admin:
    settings = get_settings()
    email = settings.super_admin_email
    admin = db.scalar(select(Admin).where(Admin.email == email))
    if admin:
        admin.role = 'SUPER_ADMIN'
        admin.full_name = settings.super_admin_full_name
        admin.password_hash = get_password_hash(settings.super_admin_password)
        admin.is_active = True
    else:
        admin = Admin(
            email=email,
            password_hash=get_password_hash(settings.super_admin_password),
            full_name=settings.super_admin_full_name,
            role='SUPER_ADMIN',
            is_active=True,
        )
        db.add(admin)

    demo_admin = db.scalar(select(Admin).where(Admin.email == 'operador@sig.local'))
    if not demo_admin:
        demo_admin = Admin(
            email='operador@sig.local',
            password_hash=get_password_hash(DEMO_PASSWORD),
            full_name='Operador Demo',
            role='ADMIN',
            is_active=True,
        )
        db.add(demo_admin)

    db.flush()
    print('[seed_all] Admins')
    return admin


def seed_users(db) -> User:
    user = db.scalar(select(User).where(User.email == 'usuario@sig.local'))
    if user:
        user.password_hash = get_password_hash(DEMO_PASSWORD)
        user.names = 'María'
        user.last_names = 'López'
        user.phone = '70012345'
        user.is_active = True
    else:
        user = User(
            email='usuario@sig.local',
            password_hash=get_password_hash(DEMO_PASSWORD),
            names='María',
            last_names='López',
            phone='70012345',
            is_active=True,
        )
        db.add(user)

    extra = db.scalar(select(User).where(User.email == 'juan@sig.local'))
    if not extra:
        db.add(
            User(
                email='juan@sig.local',
                password_hash=get_password_hash(DEMO_PASSWORD),
                names='Juan',
                last_names='Pérez',
                phone='70123456',
                is_active=True,
            )
        )

    db.flush()
    print('[seed_all] Users')
    return user


def seed_drivers(db) -> tuple[Driver, Driver]:
    approved = db.scalar(select(Driver).where(Driver.email == 'conductor@sig.local'))
    if approved:
        approved.password_hash = get_password_hash(DEMO_PASSWORD)
        approved.full_name = 'Carlos Mendoza'
        approved.approval_status = 'APPROVED'
        approved.is_active = True
    else:
        approved = Driver(
            email='conductor@sig.local',
            password_hash=get_password_hash(DEMO_PASSWORD),
            ci='1234567-SC',
            full_name='Carlos Mendoza',
            birth_date=date(1985, 3, 15),
            sex='M',
            phone='70234567',
            license_category='C',
            approval_status='APPROVED',
            is_active=True,
        )
        db.add(approved)

    pending = db.scalar(select(Driver).where(Driver.email == 'nuevo.conductor@sig.local'))
    if not pending:
        pending = Driver(
            email='nuevo.conductor@sig.local',
            password_hash=get_password_hash(DEMO_PASSWORD),
            ci='7654321-SC',
            full_name='Ana Ríos',
            birth_date=date(1990, 7, 22),
            sex='F',
            phone='70345678',
            license_category='C',
            approval_status='PENDING',
            is_active=True,
        )
        db.add(pending)

    db.flush()
    print('[seed_all] Drivers')
    return approved, pending


def seed_buses(db, linea_100: Linea) -> Bus:
    bus = db.scalar(select(Bus).where(Bus.plate == 'SCZ-1001'))
    if bus:
        bus.model = 'Toyota Coaster'
        bus.seats_count = 25
        bus.internal_number = 'M-1001'
        bus.current_line_id = linea_100.id_linea
        bus.status = 'ACTIVE'
    else:
        bus = Bus(
            plate='SCZ-1001',
            model='Toyota Coaster',
            seats_count=25,
            internal_number='M-1001',
            current_line_id=linea_100.id_linea,
            status='ACTIVE',
        )
        db.add(bus)

    spare = db.scalar(select(Bus).where(Bus.plate == 'SCZ-1002'))
    if not spare:
        db.add(
            Bus(
                plate='SCZ-1002',
                model='Mercedes Sprinter',
                seats_count=20,
                internal_number='M-1002',
                current_line_id=linea_100.id_linea,
                status='INACTIVE',
            )
        )

    db.flush()
    print('[seed_all] Buses')
    return bus


def seed_assignments(db, bus: Bus, driver: Driver) -> BusDriverAssignment:
    assignment = db.scalar(
        select(BusDriverAssignment).where(
            BusDriverAssignment.bus_id == bus.id,
            BusDriverAssignment.driver_id == driver.id,
            BusDriverAssignment.is_active.is_(True),
        )
    )
    if not assignment:
        assignment = BusDriverAssignment(
            bus_id=bus.id,
            driver_id=driver.id,
            assigned_at=datetime.now() - timedelta(days=30),
            is_active=True,
        )
        db.add(assignment)

    db.flush()
    print('[seed_all] Bus-driver assignments')
    return assignment


def seed_active_trip(db, driver: Driver, bus: Bus, linea: Linea, ruta: LineaRuta) -> ActiveTrip:
    trip = db.scalar(
        select(ActiveTrip).where(
            ActiveTrip.driver_id == driver.id,
            ActiveTrip.status == 'ACTIVE',
        )
    )
    if not trip:
        trip = ActiveTrip(
            driver_id=driver.id,
            bus_id=bus.id,
            line_id=linea.id_linea,
            route_id=ruta.id_linea_ruta,
            started_at=datetime.now() - timedelta(minutes=15),
            status='ACTIVE',
            created_at=datetime.now() - timedelta(minutes=15),
        )
        db.add(trip)
        db.flush()

    existing_locations = db.scalars(
        select(TrackingLocation).where(TrackingLocation.active_trip_id == trip.id)
    ).all()
    if not existing_locations:
        base_lng, base_lat = PLAZA_24
        for i in range(3):
            db.add(
                TrackingLocation(
                    active_trip_id=trip.id,
                    location=_point(base_lng + i * 0.001, base_lat + i * 0.0005),
                    speed=Decimal('25.00'),
                    recorded_at=datetime.now() - timedelta(minutes=10 - i * 2),
                )
            )

    db.flush()
    print('[seed_all] Active trips & tracking')
    return trip


def seed_user_data(db, user: User) -> None:
    favorite = db.scalar(
        select(FavoritePlace).where(FavoritePlace.user_id == user.id, FavoritePlace.name == 'Casa')
    )
    if not favorite:
        db.add(
            FavoritePlace(
                user_id=user.id,
                name='Casa',
                location=_point(*EQUIPETROL),
            )
        )

    history = db.scalar(
        select(UserRouteHistory).where(
            UserRouteHistory.user_id == user.id,
            UserRouteHistory.estimated_time == 28,
        )
    )
    if not history:
        db.add(
            UserRouteHistory(
                user_id=user.id,
                origin=_point(*PLAZA_24),
                destination=_point(*EQUIPETROL),
                estimated_time=28,
                walking_distance_m=Decimal('450.00'),
                transfers_count=1,
                route_summary_json={
                    'lines': ['100', '101'],
                    'total_distance_km': 8.5,
                },
                created_at=datetime.now() - timedelta(days=2),
            )
        )

    db.flush()
    print('[seed_all] Favorites & route history')


def seed_operational(db, admin: Admin) -> None:
    audit = db.scalar(
        select(AuditLog).where(AuditLog.action == 'SEED_DEMO_DATA', AuditLog.entity == 'SYSTEM')
    )
    if not audit:
        db.add(
            AuditLog(
                actor_id=admin.id,
                actor_type='ADMIN',
                action='SEED_DEMO_DATA',
                entity='SYSTEM',
                detail={'source': 'seed_all.py'},
                created_at=datetime.now(),
            )
        )

    file_import = db.scalar(select(FileImport).where(FileImport.file_name == 'DatosLineas_demo.xls'))
    if not file_import:
        db.add(
            FileImport(
                file_name='DatosLineas_demo.xls',
                status='CONFIRMED',
                total_rows=120,
                valid_rows=118,
                invalid_rows=2,
                error_report={'rows': [45, 89]},
                created_by=admin.id,
                created_at=datetime.now() - timedelta(days=7),
                confirmed_at=datetime.now() - timedelta(days=7),
            )
        )

    package = db.scalar(select(OfflinePackage).where(OfflinePackage.version == '2026.01-demo'))
    if not package:
        db.add(
            OfflinePackage(
                version='2026.01-demo',
                status='PUBLISHED',
                file_url='https://storage.example.com/offline/2026.01-demo.zip',
                file_size_bytes=15_728_640,
                package_metadata={'lines_count': 3, 'points_count': 4},
                generated_at=datetime.now() - timedelta(days=1),
                published_at=datetime.now() - timedelta(days=1),
            )
        )

    for key, value, description in [
        ('app.maintenance_mode', {'enabled': False}, 'Modo mantenimiento global'),
        ('routing.max_transfers', {'value': 3}, 'Máximo de trasbordos permitidos'),
        ('tracking.batch_interval_sec', {'value': 10}, 'Intervalo de envío GPS'),
    ]:
        setting = db.scalar(select(Setting).where(Setting.key == key))
        if setting:
            setting.value = value
            setting.description = description
            setting.updated_at = datetime.now()
        else:
            db.add(
                Setting(
                    key=key,
                    value=value,
                    description=description,
                    updated_at=datetime.now(),
                )
            )

    db.flush()
    print('[seed_all] Audit, imports, offline packages & settings')


def main() -> None:
    with SessionLocal() as db:
        transport = seed_transport(db)
        admin = seed_admins(db)
        user = seed_users(db)
        approved_driver, _ = seed_drivers(db)
        bus = seed_buses(db, transport['linea_100'])
        seed_assignments(db, bus, approved_driver)
        seed_active_trip(
            db,
            approved_driver,
            bus,
            transport['linea_100'],
            transport['ruta_100'],
        )
        seed_user_data(db, user)
        seed_operational(db, admin)
        db.commit()

    print('[seed_all] Done. Demo credentials password:', DEMO_PASSWORD)
    print('[seed_all] Super admin:', get_settings().super_admin_email)


if __name__ == '__main__':
    main()
