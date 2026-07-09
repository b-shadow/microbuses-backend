from dataclasses import dataclass


@dataclass
class AppException(Exception):
    message: str
    error_code: str
    status_code: int = 400
    details: dict | None = None
