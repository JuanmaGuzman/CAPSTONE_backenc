import pytest
from unittest.mock import Mock
from ninja.testing import TestClient
from django.contrib.sessions.middleware import SessionMiddleware
from conf.api import api
from datetime import date


@pytest.fixture(scope="session")
def ninja_client() -> TestClient:
    class SessionTestClient(TestClient):
        def _build_request(
            self, method: str, path: str, data: dict, request_params: dict
        ) -> Mock:
            request = super()._build_request(
                method,
                path,
                data,
                request_params
            )
            SessionMiddleware().process_request(request)
            request.sessions.save()
            return request
    return SessionTestClient(api)


@pytest.fixture(scope="session")
def super_user() -> Mock:
    return Mock(
        id=9001,
        is_authenticated=True,
        has_perm=Mock(return_value=True)
    )


@pytest.fixture(scope="session")
def mid_user() -> Mock:
    return Mock(
        id=8999,
        is_authenticated=True,
        has_perm=Mock(return_value=False)
    )


@pytest.fixture(scope="session")
def user_one() -> Mock:
    return Mock(id=1, is_authenticated=True)


@pytest.fixture(scope="session")
def user_one_creation_info() -> dict:
    return {
        'username': 'js',
        'email': 'js@email.com',
        'first_name': 'John',
        'last_name': 'Smith',
        'phone_number': '+569000001',
        'rut': '00000000-1',
        'birthdate': date.today(),
        'password1': 'password',
        'password2': 'password'
    }


@pytest.fixture(scope="session")
def user_one_get_info() -> dict:
    return {
        'id': 1,
        'username': 'js',
        'email': 'js@email.com',
        'first_name': 'John',
        'last_name': 'Smith',
        'phone_number': '+569000001',
        'rut': '00000000-1',
        'birthdate': date.today().isoformat(),
        'is_admin': False,
        'is_seller': False
    }


@pytest.fixture(scope="session")
def user_two() -> Mock:
    return Mock(id=2, is_authenticated=True)


@pytest.fixture(scope="session")
def user_two_creation_info() -> dict:
    return {
        'username': 'js2',
        'email': 'js2@email.com',
        'first_name': 'John2',
        'last_name': 'Smith2',
        'phone_number': '+569000002',
        'rut': '00000000-2',
        'birthdate': date.today(),
        'password1': 'password',
        'password2': 'password'
    }


@pytest.fixture(scope="session")
def user_two_get_info() -> dict:
    return {
        'id': 2,
        'username': 'js2',
        'email': 'js2@email.com',
        'first_name': 'John2',
        'last_name': 'Smith2',
        'phone_number': '+569000002',
        'rut': '00000000-2',
        'birthdate': date.today().isoformat(),
        'is_admin': False,
        'is_seller': False
    }


@pytest.fixture(scope="session")
def address_creation_info():
    return {
        'region': 'RegionTest',
        'commune': 'CommuneTest',
        'address': 'AddressTest'
    }
