from sqlalchemy.orm import Session

from app.modules.nearby_lines.repository import find_lines_near_point


class NearbyLinesService:
    def search(self, db: Session, lat: float, lng: float, radius_m: float):
        return find_lines_near_point(db, lat=lat, lng=lng, radius_m=radius_m)
