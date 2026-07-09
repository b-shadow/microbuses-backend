from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_actor, get_db
from app.core.permissions import require_roles
from app.modules.buses.models import Bus
from app.modules.bus_assignments.models import BusDriverAssignment
from app.modules.drivers.models import Driver
from app.modules.lines.models import Linea
from app.modules.routes.models import LineaRuta
from app.modules.stops.models import Punto
from app.modules.users.models import User
from app.modules.active_trips.models import ActiveTrip
from app.shared.responses.helpers import ok

router = APIRouter(prefix='/dashboard', tags=['dashboard'])


@router.get('/admin')
def admin_dashboard(actor=Depends(get_current_actor), db: Session = Depends(get_db)):
    require_roles(actor, {'ADMIN', 'SUPER_ADMIN'})

    # --- Counts ---
    total_drivers = db.scalar(select(func.count()).select_from(Driver)) or 0
    total_buses = db.scalar(select(func.count()).select_from(Bus)) or 0
    total_lineas = db.scalar(select(func.count()).select_from(Linea)) or 0
    total_rutas = db.scalar(select(func.count()).select_from(LineaRuta)) or 0
    total_stops = db.scalar(select(func.count()).select_from(Punto)) or 0
    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    total_assignments = db.scalar(
        select(func.count()).select_from(BusDriverAssignment).where(BusDriverAssignment.is_active == True)
    ) or 0
    active_trips = db.scalar(
        select(func.count()).select_from(ActiveTrip).where(ActiveTrip.status == 'ACTIVE')
    ) or 0

    # --- Driver approval breakdown ---
    driver_pending = db.scalar(
        select(func.count()).select_from(Driver).where(Driver.approval_status == 'PENDING')
    ) or 0
    driver_approved = db.scalar(
        select(func.count()).select_from(Driver).where(Driver.approval_status == 'APPROVED')
    ) or 0
    driver_rejected = db.scalar(
        select(func.count()).select_from(Driver).where(Driver.approval_status == 'REJECTED')
    ) or 0

    # --- Bus status breakdown ---
    bus_active = db.scalar(
        select(func.count()).select_from(Bus).where(Bus.status == 'ACTIVE')
    ) or 0
    bus_inactive = db.scalar(
        select(func.count()).select_from(Bus).where(Bus.status == 'INACTIVE')
    ) or 0

    # --- Recent drivers (last 5) ---
    recent_drivers_rows = db.execute(
        select(Driver.id, Driver.full_name, Driver.email, Driver.approval_status, Driver.created_at)
        .order_by(Driver.created_at.desc())
        .limit(5)
    ).all()
    recent_drivers = [
        {
            'id': str(r.id),
            'full_name': r.full_name,
            'email': r.email,
            'approval_status': r.approval_status,
            'created_at': r.created_at.isoformat() if r.created_at else None,
        }
        for r in recent_drivers_rows
    ]

    # --- Recent lines (last 5) ---
    recent_lines_rows = db.execute(
        select(Linea.id_linea, Linea.nombre_linea, Linea.color_linea, Linea.fecha_creacion)
        .order_by(Linea.fecha_creacion.desc())
        .limit(5)
    ).all()
    recent_lines = [
        {
            'id': r.id_linea,
            'nombre': r.nombre_linea,
            'color': r.color_linea,
            'created_at': r.fecha_creacion.isoformat() if r.fecha_creacion else None,
        }
        for r in recent_lines_rows
    ]

    return ok(
        data={
            'counts': {
                'drivers': total_drivers,
                'buses': total_buses,
                'lineas': total_lineas,
                'rutas': total_rutas,
                'stops': total_stops,
                'users': total_users,
                'assignments': total_assignments,
                'active_trips': active_trips,
            },
            'driver_status': {
                'pending': driver_pending,
                'approved': driver_approved,
                'rejected': driver_rejected,
            },
            'bus_status': {
                'active': bus_active,
                'inactive': bus_inactive,
            },
            'recent_drivers': recent_drivers,
            'recent_lines': recent_lines,
        }
    )
