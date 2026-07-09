from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog


def log_event(
    db: Session,
    *,
    actor_id: UUID | None,
    actor_type: str,
    action: str,
    entity: str,
    entity_id: UUID | None,
    detail: dict[str, Any] | None = None,
) -> None:
    row = AuditLog(
        actor_id=actor_id,
        actor_type=actor_type,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail,
        created_at=datetime.utcnow(),
    )
    db.add(row)


def list_logs(db: Session, limit: int = 100, actor_id: UUID | None = None) -> list[AuditLog]:
    query = select(AuditLog)
    if actor_id is not None:
        query = query.where(AuditLog.actor_id == actor_id)
    query = query.order_by(AuditLog.created_at.desc()).limit(limit)
    return list(db.scalars(query))
