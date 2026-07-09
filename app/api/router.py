from fastapi import APIRouter

from app.modules.active_trips.router import router as active_trips_router
from app.modules.admins.router import router as admins_router
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.buses.router import router as buses_router
from app.modules.bus_assignments.router import router as bus_assignments_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.drivers.router import router as drivers_router
from app.modules.favorites.router import router as favorites_router
from app.modules.file_imports.router import router as file_imports_router
from app.modules.lines.router import router as lines_router
from app.modules.nearby_lines.router import router as nearby_lines_router
from app.modules.offline_packages.router import router as offline_packages_router
from app.modules.route_points.router import router as route_points_router
from app.modules.routes.router import router as routes_router
from app.modules.routing_engine.router import router as routing_engine_router
from app.modules.settings.router import router as settings_router
from app.modules.stops.router import router as stops_router
from app.modules.tracking.router import router as tracking_router
from app.modules.users.router import router as users_router
from app.modules.user_history.router import router as user_history_router
from app.modules.walking_network.router import router as walking_network_router
from app.modules.variants.router import router as variants_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(admins_router)
api_router.include_router(drivers_router)
api_router.include_router(lines_router)
api_router.include_router(routes_router)
api_router.include_router(route_points_router)
api_router.include_router(stops_router)
api_router.include_router(nearby_lines_router)
api_router.include_router(routing_engine_router)
api_router.include_router(walking_network_router)
api_router.include_router(buses_router)
api_router.include_router(bus_assignments_router)
api_router.include_router(active_trips_router)
api_router.include_router(tracking_router)
api_router.include_router(favorites_router)
api_router.include_router(user_history_router)
api_router.include_router(offline_packages_router)
api_router.include_router(file_imports_router)
api_router.include_router(dashboard_router)
api_router.include_router(audit_router)
api_router.include_router(settings_router)
api_router.include_router(variants_router)
