import pytest

from app.core.exceptions import AppException
from app.core.permissions import require_roles, resolve_role


class User:
    role = None


class Driver:
    role = None


class Admin:
    def __init__(self, role: str):
        self.role = role


def test_resolve_role_user():
    assert resolve_role(User()) == 'USER'


def test_resolve_role_driver():
    assert resolve_role(Driver()) == 'DRIVER'


def test_require_roles_raises_for_none_actor():
    with pytest.raises(AppException) as exc:
        require_roles(None, {'ADMIN'})
    assert exc.value.error_code == 'UNAUTHENTICATED'


def test_require_roles_allows_matching_role():
    require_roles(Admin('SUPER_ADMIN'), {'SUPER_ADMIN'})


def test_require_roles_blocks_non_matching_role():
    with pytest.raises(AppException) as exc:
        require_roles(Admin('ADMIN'), {'SUPER_ADMIN'})
    assert exc.value.error_code == 'FORBIDDEN'
