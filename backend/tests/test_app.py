from http import HTTPStatus

from fastapi.testclient import TestClient


def test_root_deve_retornar_ok(client: TestClient):
    response = client.get('/')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'ola': 'mundo'}
