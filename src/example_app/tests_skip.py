from ninja.testing import TestClient
from conf.api import api


def test_hello_world():
    client = TestClient(api)
    response = client.get('/')

    assert response.status_code == 200
    assert response.json()['hello'] == 'world'
