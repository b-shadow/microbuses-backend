from enum import StrEnum


class Role(StrEnum):
    USER = 'USER'
    DRIVER = 'DRIVER'
    ADMIN = 'ADMIN'
    SUPER_ADMIN = 'SUPER_ADMIN'
