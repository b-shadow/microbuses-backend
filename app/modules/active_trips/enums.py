from enum import StrEnum


class ActiveTripStatus(StrEnum):
    ACTIVE = 'ACTIVE'
    FINISHED = 'FINISHED'
    CANCELLED = 'CANCELLED'
