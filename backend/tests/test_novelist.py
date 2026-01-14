import random
from datetime import timedelta
from http import HTTPStatus
from secrets import token_urlsafe
from typing import Awaitable, Callable
from unittest.mock import patch
from urllib.parse import urlencode

import factory
import ipdb  # noqa: F401
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from madr.app import app
from madr.models.book import Book
from madr.models.novelist import Novelist
from tests.factories import NovelistFactory
from tests.utils import frozen_context

url_base = '/novelists/'


# ============================================================================
# CREATE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_create_novelist_deve_retornar_novelist_com_id(
    client, authenticated_token
):
    payload = {'name': 'Zaraulstra'}
    response = client.post(
        url_base,
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {**payload, 'id': 1}


@pytest.mark.asyncio
async def test_create_novelist_deve_falhar_retornar_conflito(
    client, authenticated_token, novelist
):
    payload = {'name': novelist.name}
    response = client.post(
        url_base,
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Novelist already exists'}


@pytest.mark.asyncio
async def test_create_novelist_deve_falhar_com_nao_autorizacao(client):
    payload = {'name': 'Zaraulstra'}
    response = client.post(url_base, json=payload, headers={})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


@pytest.mark.asyncio
async def test_create_novelist_deve_falhar_com_token_expirado(
    session, client, authenticated_token
):
    payload = {'name': 'Zaraulstra da Bahia'}

    with frozen_context(timedelta(minutes=31)):
        response = client.post(
            url_base,
            json=payload,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Expired token'}

        db_novelist = await session.scalar(
            select(Novelist).where(Novelist.name == payload['name'])
        )
        assert db_novelist is None


@pytest.mark.asyncio
async def test_create_novelist_deve_falhar_com_erro_de_banco(
    authenticated_token, user, client, session
):
    with patch.object(
        session,
        'commit',
        side_effect=SQLAlchemyError('Generic Error DB'),
    ):
        response = client.post(
            url_base,
            json={'name': 'Test Novelist'},
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Database error'}


@pytest.mark.asyncio
async def test_create_novelist_deve_falhar_com_nome_vazio(
    client, authenticated_token
):
    payload = {'name': None}
    response = client.post(
        url_base,
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ============================================================================
# UPDATE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_update_novelist_deve_retornar_novelist_modificado(
    client, novelist, authenticated_token
):
    modified_name = f'modified_{novelist.name}'
    payload = {'name': modified_name}

    response = client.put(
        f'{url_base}{novelist.id}',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['name'] == modified_name


@pytest.mark.asyncio
async def test_update_novelist_deve_falhar_com_not_found(
    client, novelist, authenticated_token
):
    payload = {'name': f'modified_{novelist.name}'}

    response = client.put(
        f'{url_base}{novelist.id + 89749}',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Novelist not found'}


@pytest.mark.asyncio
async def test_update_novelist_deve_falhar_unique_violation(
    client, session, authenticated_token
):
    novelist1 = Novelist(name='Novelist One')
    novelist2 = Novelist(name='Novelist Two')
    session.add_all([novelist1, novelist2])
    await session.commit()

    response = client.put(
        f'{url_base}{novelist2.id}',
        json={'name': novelist1.name},
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Novelist already exists'}


@pytest.mark.asyncio
async def test_update_novelist_deve_falhar_com_rollback(
    session, client, novelist_with_books, authenticated_token, novelist
):
    auth_header = {
        'Authorization': f'Bearer {authenticated_token.access_token}'
    }

    novelists = [await novelist_with_books(1) for _ in range(13)]
    # ipdb.set_trace()
    random_novelist = random.choice(novelists)

    # tentativa de mudar o nome para um nome que já existe
    response = client.put(
        f'{url_base}{novelist.id}',
        json={'name': random_novelist.name},
        headers=auth_header,
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Novelist already exists'}
    await session.refresh(novelist)
    await session.refresh(random_novelist)
    assert novelist.name != random_novelist.name


@pytest.mark.asyncio
async def test_update_novelist_deve_falhar_com_token_expirado(
    session, client, novelist, authenticated_token
):
    modified_name = f'modified_{novelist.name}'
    payload = {'name': modified_name}

    with frozen_context(timedelta(minutes=31)):
        response = client.put(
            f'{url_base}{novelist.id}',
            json=payload,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Expired token'}

        db_novelist = await session.scalar(
            select(Novelist).where(Novelist.name == payload['name'])
        )
        assert db_novelist is None


@pytest.mark.asyncio
async def test_update_novelist_sem_mudancas_deve_ter_sucesso(
    client, novelist, authenticated_token
):
    payload = {'name': novelist.name}
    response = client.put(
        f'{url_base}{novelist.id}',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['name'] == novelist.name


@pytest.mark.asyncio
async def test_update_novelist_com_payload_vazio_deve_ter_sucesso(
    client, novelist, authenticated_token
):
    original_name = novelist.name
    response = client.put(
        f'{url_base}{novelist.id}',
        json={},
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['name'] == original_name


# ============================================================================
# READ TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_read_novelists_sem_filtros_deve_retornar_todos(client, session):
    limit = 17
    novelists = NovelistFactory.build_batch(limit)
    session.add_all(novelists)
    await session.commit()
    response = client.get(f'{url_base}?limit={limit}')
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK

    assert len(response_data['data']) == limit
    assert response_data['total'] == limit


@pytest.mark.asyncio
async def test_read_novelists_com_limit_deve_respeitar_limite(client, session):
    novelists = NovelistFactory.build_batch(50)
    session.add_all(novelists)
    await session.commit()

    response = client.get(f'{url_base}?limit=10')
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert len(response_data['data']) == 10  # noqa: PLR2004
    assert response_data['total'] == 50  # noqa: PLR2004


@pytest.mark.asyncio
async def test_read_novelists_com_paginacao_deve_retornar_pagina_correta(
    client, session
):
    novelists = NovelistFactory.build_batch(30)
    session.add_all(novelists)
    await session.commit()

    response = client.get(f'{url_base}?limit=10&page=2')
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert len(response_data['data']) == 10  # noqa: PLR2004
    assert response_data['page'] == 2  # noqa: PLR2004
    assert response_data['hasPrev'] is True
    assert response_data['hasNext'] is True


@pytest.mark.asyncio
async def test_read_novelists_ultima_pagina_deve_indicar_sem_proxima(
    client, session
):
    novelists = NovelistFactory.build_batch(25)
    session.add_all(novelists)
    await session.commit()

    response = client.get(f'{url_base}?limit=10&page=3')
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert len(response_data['data']) == 5  # noqa: PLR2004
    assert response_data['hasNext'] is False
    assert response_data['hasPrev'] is True


@pytest.mark.asyncio
async def test_read_novelists_by_filters_pagination_ordenation_deve_ter_sucesso(  # noqa: E501
    client, session, novelist_with_books
):
    total_novelists_with_match = 50
    limit = 10
    [(await novelist_with_books(8)) for _ in range(70)]

    partial_name = token_urlsafe(10)
    uri = '?' + urlencode({'name': partial_name, 'limit': limit})
    novelists = NovelistFactory.build_batch(
        size=total_novelists_with_match,
        name=factory.Sequence(  # type: ignore
            lambda n: (
                f'{token_urlsafe(10)}_{partial_name}+-{n}*{token_urlsafe(10)}'
            )
        ),
    )
    session.add_all(novelists)
    await session.commit()
    url = url_base + uri
    response = client.get(url)

    response_data = response.json()
    data = response_data['data']

    assert len(data) == limit
    assert response_data['total'] == total_novelists_with_match
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_read_novelists_by_filters_pagination_ordenation_deve_ter_sucesso_retornar_vazio(  # noqa: E501
    client, session, novelist_with_books
):
    total_novelists_with_match = 72
    limit = 10
    [await novelist_with_books(8) for _ in range(70)]

    partial_name = token_urlsafe(10)
    uri = '?' + urlencode({'name': 'nome inexistente', 'limit': limit})
    novelists = NovelistFactory.build_batch(
        size=total_novelists_with_match,
        name=factory.Sequence(  # type: ignore
            lambda n: (
                f'{token_urlsafe(10)}_{partial_name}+-{n}*{token_urlsafe(10)}'
            )
        ),
    )
    session.add_all(novelists)
    await session.commit()
    url = url_base + uri
    response = client.get(url)

    response_data = response.json()
    data = response_data['data']

    assert len(data) == 0
    assert response_data['total'] == 0
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_read_novelists_filtro_nome_case_insensitive(client, session):
    novelist1 = Novelist(name='Jorge Amado')
    novelist2 = Novelist(name='Machado de Assis')
    novelist3 = Novelist(name='Clarice Lispector')
    session.add_all([novelist1, novelist2, novelist3])
    await session.commit()

    response = client.get(f'{url_base}?name=JORGE')
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert len(response_data['data']) == 1
    assert response_data['data'][0]['name'] == 'Jorge Amado'


@pytest.mark.asyncio
async def test_read_novelists_filtro_nome_com_espacos_deve_funcionar(
    client, session
):
    novelist1 = Novelist(name='Jorge Amado')
    session.add(novelist1)
    await session.commit()

    response = client.get(f'{url_base}?name=  Jorge  ')
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert len(response_data['data']) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('order_dir', ['asc', 'desc'])
@pytest.mark.parametrize('order_by', ['id', 'name'])
async def test_read_novelists_ordenacao_deve_funcionar(
    client, session, order_by, order_dir
):
    novelists = [
        Novelist(name='Zélia'),
        Novelist(name='Ana'),
        Novelist(name='Maria'),
    ]
    session.add_all(novelists)
    await session.commit()

    response = client.get(
        f'{url_base}?orderBy={order_by}&orderDir={order_dir}'
    )
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    sorted_data = sorted(
        response_data['data'],
        key=lambda n: n[order_by],
        reverse=(order_dir == 'desc'),
    )
    assert response_data['data'] == sorted_data


@pytest.mark.asyncio
async def test_read_novelists_vazio_deve_retornar_lista_vazia(client):
    response = client.get(url_base)
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert response_data['data'] == []
    assert response_data['total'] == 0


# ============================================================================
# READ BOOKS OF NOVELIST TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_read_books_of_novelist_deve_retornar_lista_de_livros_de_um_romancista(  # noqa: E501
    client, novelist_with_books: Callable[..., Awaitable[Novelist]]
):
    novelist = await novelist_with_books(350)
    response = client.get(f'{url_base}{novelist.id}/books')
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert len(response_data['data']) > 0


@pytest.mark.asyncio
async def test_read_books_of_novelist_deve_retornar_livros_de_um_romancista_com_limit_e_offset(  # noqa: E501
    client, novelist_with_books: Callable[..., Awaitable[Novelist]]
):
    total_books = 43
    limit = 8
    page = 6
    params = {'limit': limit, 'page': page}
    query_string = urlencode(params)

    partial_page_qty = total_books - ((page - 1) * limit)

    novelist = await novelist_with_books(total_books)

    url = f'{url_base}{novelist.id}/books?{query_string}'
    response = client.get(url)
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert len(response_data['data']) == partial_page_qty


@pytest.mark.asyncio
async def test_read_books_of_novelist_deve_retornar_0_livros_por_pagina_inexistente(  # noqa: E501
    client, novelist_with_books: Callable[..., Awaitable[Novelist]]
):
    total_books = 25
    limit = 10
    page = 4
    params = {'limit': limit, 'page': page}
    query_string = urlencode(params)
    novelist = await novelist_with_books(total_books)

    url = f'{url_base}{novelist.id}/books?{query_string}'
    response = client.get(url)
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert response_data == {
        'data': [],
        'total': 0,
        'page': page,
        'hasPrev': True,
        'hasNext': False,
    }


@pytest.mark.asyncio
async def test_read_books_of_novelist_deve_retornar_0_livros_por_pagina_muito_acima_da_ultima_existente(  # noqa: E501
    client, novelist_with_books: Callable[..., Awaitable[Novelist]]
):
    total_books = 50
    limit = 10
    page = 9
    params = {'limit': limit, 'page': page}
    query_string = urlencode(params)

    novelist = await novelist_with_books(total_books)

    url = f'{url_base}{novelist.id}/books?{query_string}'
    response = client.get(url)
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert response_data == {
        'data': [],
        'total': 0,
        'page': page,
        'hasPrev': True,
        'hasNext': False,
    }


@pytest.mark.asyncio
async def test_read_books_of_novelist_deve_retornar_zero_livros_de_um_romancista(  # noqa: E501
    client, novelist_with_books: Callable[..., Awaitable[Novelist]]
):
    total_books = 0
    params = {'limit': 10, 'page': 6}
    query_string = urlencode(params)
    novelist = await novelist_with_books(total_books)

    url = f'{url_base}{novelist.id}/books?{query_string}'
    response = client.get(url)

    response_data = response.json()
    assert response.status_code == HTTPStatus.OK
    assert len(response_data['data']) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('order_dir', ['asc', 'desc'])
@pytest.mark.parametrize('order_by', ['title', 'name', 'year'])
async def test_read_books_of_novelist_deve_retornar_livros_ordenados(
    client,
    novelist_with_books: Callable[..., Awaitable[Novelist]],
    order_by,
    order_dir,
):
    total_books = 50
    params = {
        'limit': 8,
        'page': 5,
        'orderBy': order_by,
        'orderDir': order_dir,
    }
    query_string = urlencode(params)
    novelist = await novelist_with_books(
        total_books, 'book_name', 'book_title'
    )

    url = f'{url_base}{novelist.id}/books?{query_string}'
    response = client.get(url)
    response_data = response.json()
    assert response.status_code == HTTPStatus.OK

    sorted_data = sorted(
        response_data['data'],
        key=lambda book: book[order_by],
        reverse=(order_dir == 'desc'),
    )
    assert response_data['data'] == sorted_data


@pytest.mark.asyncio
async def test_read_books_of_novelist_primeira_pagina_deve_indicar_sem_anterior(  # noqa: E501
    client, novelist_with_books: Callable[..., Awaitable[Novelist]]
):
    novelist = await novelist_with_books(50)
    response = client.get(f'{url_base}{novelist.id}/books?limit=10&page=1')
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert response_data['hasPrev'] is False
    assert response_data['hasNext'] is True


@pytest.mark.asyncio
async def test_read_books_of_novelist_com_id_inexistente_deve_retornar_vazio(
    client, session
):
    stmt = select(func.max(Novelist.id))
    max_id = await session.scalar(stmt)
    inexistent_id = (max_id or 0) + 1

    response = client.get(f'{url_base}{inexistent_id}/books')
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert response_data['data'] == []
    assert response_data['total'] == 0


# ============================================================================
# DELETE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_delete_novelist_deve_retornar_success_delecao(
    client,
    authenticated_token,
    novelist_with_books: Callable[..., Awaitable[Novelist]],
):
    novelist = await novelist_with_books(25)
    response = client.delete(
        f'{url_base}{novelist.id}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Novelist Removed'}


@pytest.mark.asyncio
async def test_delete_novelist_e_livros_deve_retornar_success(
    client,
    authenticated_token,
    session,
    novelist_with_books: Callable[..., Awaitable[Novelist]],
):
    novelist = await novelist_with_books(15)
    novelist_id = novelist.id

    response = client.delete(
        f'{url_base}{novelist_id}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Novelist Removed'}

    db_books = (
        await session.scalars(
            select(Book).where(Book.id_novelist == novelist_id)
        )
    ).all()
    assert len(db_books) == 0


@pytest.mark.asyncio
async def test_delete_novelist_deve_retornar_not_found(
    session,
    client,
    authenticated_token,
    novelist_with_books: Callable[..., Awaitable[Novelist]],
):
    novelist = await novelist_with_books(15)
    stmt = select(func.max(Novelist.id))
    max_id = await session.scalar(stmt)
    last_id_novelist = 0 if max_id is None else max_id

    response = client.delete(
        f'{url_base}{last_id_novelist + 1}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    db_novelist = await session.scalar(
        select(Novelist).where(Novelist.id == novelist.id)
    )
    assert db_novelist
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Novelist not found'}


@pytest.mark.asyncio
async def test_delete_novelist_deve_retornar_unauthorized(
    client, novelist_with_books: Callable[..., Awaitable[Novelist]]
):
    novelist = await novelist_with_books(15)
    response = client.delete(f'{url_base}{novelist.id}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


@pytest.mark.asyncio
async def test_delete_novelist_com_token_expirado_deve_falhar(
    client, novelist, authenticated_token
):
    with frozen_context(timedelta(minutes=31)):
        response = client.delete(
            f'{url_base}{novelist.id}',
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Expired token'}


@pytest.mark.asyncio
async def test_delete_novelist_sem_livros_deve_ter_sucesso(
    client, authenticated_token, session
):
    novelist = Novelist(name='Test Novelist')
    session.add(novelist)
    await session.commit()

    response = client.delete(
        f'{url_base}{novelist.id}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Novelist Removed'}

    db_novelist = await session.scalar(
        select(Novelist).where(Novelist.id == novelist.id)
    )
    assert db_novelist is None


@pytest.mark.asyncio
async def test_create_novelist_deve_falhar_integrity_error_generico(
    client: TestClient, authenticated_token, user, session
):
    """Testa que IntegrityError sem unique violation não lança exceção extra"""
    headers = {'Authorization': f'Bearer {authenticated_token.access_token}'}
    # Mock is_unique_violation para retornar False
    with patch(
        'madr.api.v1.novelists.is_unique_violation', return_value=False
    ):
        with patch.object(
            session,
            'commit',
            side_effect=IntegrityError(
                'statement', 'params', Exception('check constraint')
            ),
        ):
            client = TestClient(app)
            response = client.post(
                url_base, json={'name': 'Test'}, headers=headers
            )

            assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


# @pytest.mark.asyncio
# async def test_update_novelist_deve_falhar_integrity_error_generico(
#     authenticated_token, novelist, user, session
# ):
#     headers = {'Authorization': f'Bearer {authenticated_token.access_token}'}
#     with patch(
#         'madr.api.v1.novelists.is_unique_violation', return_value=False
#     ):
#         with patch.object(
#             session,
#             'commit',
#             side_effect=IntegrityError(
#                 'statement', 'params', Exception('fk violation')
#             ),
#         ):
#             client = TestClient(app)
#             response = client.put(
#                 f'{url_base}{novelist.id}',
#                 json={'name': 'Updated'},
#                 headers=headers,
#             )

#             assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
