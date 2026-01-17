from http import HTTPStatus

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_deve_retornar_ok(client: AsyncClient):
    response = await client.get('/')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'ok'}
