from app.shared.responses.base import SuccessResponse


def ok(data=None, message: str = 'Operación realizada correctamente', meta: dict | None = None) -> SuccessResponse:
    return SuccessResponse(message=message, data={} if data is None else data, meta=meta or {})
