import pytest

from app.api.auth_dependencies import require_merchant_roles
from app.auth.roles import MerchantRole


def make_context(role):
    class Membership:
        pass

    membership = Membership()
    membership.role = role.value
    return (None, membership)


def test_rbac_allows_configured_roles():
    dependency = require_merchant_roles(
        MerchantRole.OWNER,
        MerchantRole.ADMIN,
    )

    for role in (MerchantRole.OWNER, MerchantRole.ADMIN):
        context = make_context(role)
        assert dependency(merchant_context=context) == context


def test_rbac_rejects_unconfigured_roles():
    dependency = require_merchant_roles(
        MerchantRole.OWNER,
        MerchantRole.ADMIN,
    )

    for role in (MerchantRole.OPERATOR, MerchantRole.VIEWER):
        with pytest.raises(Exception) as exc_info:
            dependency(merchant_context=make_context(role))

        assert exc_info.value.status_code == 403
