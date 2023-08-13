import pytest
from django.contrib.auth.models import Group


@pytest.fixture(scope="function")
def create_seller_permissions() -> None:
    Group.objects.get_or_create(name='Seller')


@pytest.fixture(scope="function")
def create_admin_permissions() -> None:
    Group.objects.get_or_create(name='Admin')
