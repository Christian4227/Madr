from datetime import timedelta
from http import HTTPStatus
from typing import Awaitable, Callable, Optional
from unittest.mock import Mock, patch
from urllib.parse import urlencode

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from madr.app import app
from madr.core.database import get_session
from madr.models.book import Book
from madr.models.novelist import Novelist
from madr.models.user import User
from madr.schemas.books import BookPublic
from madr.schemas.security import Token
from tests.factories import BookFactory
from tests.utils import frozen_context

base_url = '/books/'


# ============================================================================
# CREATE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_create_book_deve_ter_exito_e_retornar_book_com_id(
    client: AsyncClient,
    authenticated_token: Token,
    book_payload: dict,
):
    response = await client.post(
        base_url,
        json=book_payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    # ipdb.set_trace()
    assert response.status_code == HTTPStatus.CREATED


# @pytest.mark.asyncio
# async def test_create_book_deve_falhar_com_conflict(
#     session: AsyncSession,
#      client: AsyncClient,
#     authenticated_token: Token,
#     book: Book,
# ):
#     response = await client.post(
#         base_url,
#         json={
#             'idNovelist': book.id_novelist,
#             'name': book.name,
#             'year': '2017',
#             'title': 'Modified Title',
#         },
#         headers={
#             'Authorization': f'Bearer {authenticated_token.access_token}'
#         },
#     )

#     assert response.status_code == HTTPStatus.CONFLICT
#     assert response.json()['detail'] == 'Book already exists'

#     db_books = await session.scalars(
#         select(Book).where(Book.name == book.name)
#     ).all()
#     assert len(db_books) == 1


@pytest.mark.asyncio
async def test_create_book_deve_falhar_com_conflict(
    session: AsyncSession,
    client: AsyncClient,
    authenticated_token: Token,
    book: Book,
):
    book_name = book.name
    book_id_novelist = book.id_novelist

    response = await client.post(
        base_url,
        json={
            'idNovelist': book_id_novelist,
            'name': book_name,
            'year': '2017',
            'title': 'Modified Title',
        },
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Book already exists'

    stmt = select(Book).where(Book.name == book_name)
    result = (await session.scalars(stmt)).all()
    db_books = result
    assert len(db_books) == 1


@pytest.mark.asyncio
async def test_create_book_deve_falhar_por_nao_existir_romancista(
    session: AsyncSession,
    authenticated_token: Token,
    client: AsyncClient,
    book_payload: dict,
):
    book_payload['idNovelist'] = 99999
    response = await client.post(
        base_url,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
        json=book_payload,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Novelist not found'}

    db_book = await session.scalar(
        select(Book).where(Book.name == book_payload['name'])
    )
    assert db_book is None


@pytest.mark.asyncio
async def test_create_book_deve_falhar_sem_authorization(
    client: AsyncClient,
    book_payload: dict,
):
    response = await client.post(base_url, json=book_payload)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Not authenticated'


@pytest.mark.asyncio
async def test_create_book_deve_falhar_sem_token_valido(
    client: AsyncClient,
    book_payload: dict,
):
    response = await client.post(
        base_url,
        headers={'Authorization': 'Bearer eyasdasdasd'},
        json=book_payload,
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Could not validate credentials'


@pytest.mark.asyncio
async def test_create_book_deve_falhar_por_token_expirado(
    session: AsyncSession,
    authenticated_token: Token,
    client: AsyncClient,
    book_payload: dict,
):
    with frozen_context(timedelta(minutes=31)):
        response = await client.post(
            base_url,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
            json=book_payload,
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Expired token'}

        db_book = await session.scalar(
            select(Book).where(Book.name == book_payload['name'])
        )
        assert db_book is None


@pytest.mark.asyncio
async def test_create_book_deve_falhar_user_removido(
    authenticated_token: Token,
    book_payload: dict,
    client: AsyncClient,
    session: AsyncSession,
):
    await session.execute(delete(User))
    await session.commit()

    response = await client.post(
        base_url,
        json=book_payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


@pytest.mark.parametrize(
    'field_missing',
    ['name', 'year', 'title', 'idNovelist'],
)
@pytest.mark.asyncio
async def test_create_book_deve_falhar_sem_campos_obrigatorios(
    field_missing: str,
    client: AsyncClient,
    authenticated_token: Token,
    book_payload: dict,
):
    del book_payload[field_missing]
    response = await client.post(
        base_url,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
        json=book_payload,
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    errors = response.json()['detail']
    assert any(
        err['type'] == 'missing' and err['loc'][1] == field_missing
        for err in errors
    )


@pytest.mark.parametrize(
    'field',
    ['name', 'year', 'title', 'idNovelist'],
)
@pytest.mark.asyncio
async def test_create_book_deve_falhar_com_null_em_campos_obrigatorios(
    field: str,
    client: AsyncClient,
    authenticated_token: Token,
    book_payload: dict,
):
    book_payload[field] = None
    response = await client.post(
        base_url,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
        json=book_payload,
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    errors = response.json()['detail']
    assert any(err['loc'][1] == field for err in errors)


@pytest.mark.asyncio
async def test_create_book_deve_falhar_com_erro_de_banco_e_rollback(
    session: AsyncSession,
    authenticated_token: Token,
    book_payload: dict,
    user: User,
):
    mock_session = Mock(spec=AsyncSession)
    mock_session.scalar.return_value = user
    mock_session.commit.side_effect = SQLAlchemyError('Database error')

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as client:
        response = await client.post(
            base_url,
            json=book_payload,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Database error'}
    mock_session.rollback.assert_called_once()

    db_book = await session.scalar(
        select(Book).where(Book.name == book_payload['name'])
    )
    assert db_book is None


@pytest.mark.asyncio
async def test_create_book_deve_falhar_integrity_error_generico(
    authenticated_token: Token,
    book_payload: dict,
    user: User,
):
    mock_session = Mock(spec=AsyncSession)
    mock_session.scalar.return_value = user
    mock_session.commit.side_effect = IntegrityError(
        'statement', 'params', Exception('check constraint failed')
    )

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as client:
        response = await client.post(
            base_url,
            json=book_payload,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Integrity violation'}
    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_create_book_falha_exception_generica(
    authenticated_token: Token, book_payload: dict, user: User
):
    mock_session = Mock(spec=AsyncSession)
    mock_session.scalar.return_value = user
    mock_session.commit.side_effect = Exception('Unexpected error')

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as client:
        response = await client.post(
            base_url,
            json=book_payload,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Internal error'}


# ============================================================================
# UPDATE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_update_book_deve_ter_exito_e_retornar_book_modificado(
    client: AsyncClient,
    authenticated_token: Token,
    book: Book,
):
    payload = {'title': 'Modified Title'}
    response = await client.put(
        f'{base_url}{book.id}',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['title'] == 'Modified Title'


@pytest.mark.asyncio
async def test_update_book_deve_falhar_book_not_found(
    client: AsyncClient,
    authenticated_token: Token,
):
    payload = {'title': 'Modified Title'}
    response = await client.put(
        f'{base_url}99999',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Book not found'}


@pytest.mark.asyncio
async def test_update_book_deve_falhar_por_nao_existir_romancista(
    novelist: Novelist,
    authenticated_token: Token,
    client: AsyncClient,
    book: Book,
):
    payload = {'idNovelist': novelist.id + 10}
    response = await client.put(
        f'{base_url}{book.id}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
        json=payload,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Novelist not found'}


@pytest.mark.asyncio
async def test_update_book_deve_falhar_unique_violation(
    book: Book,
    client: AsyncClient,
    authenticated_token: Token,
    session: AsyncSession,
):
    book_name_existent = book.name

    other_book = Book(
        name='other_book',
        year=2020,
        title='Other',
        id_novelist=book.id_novelist,
    )
    session.add(other_book)
    await session.commit()

    response = await client.put(
        f'{base_url}{other_book.id}',
        json={'name': book_name_existent},
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Book already exists'}


@pytest.mark.asyncio
async def test_update_book_deve_falhar_com_erro_de_banco_e_rollback(
    authenticated_token: Token,
    user: User,
    book: Book,
):
    mock_session = Mock(spec=AsyncSession)
    mock_session.scalar.side_effect = [user, book]
    mock_session.commit.side_effect = SQLAlchemyError('DB Error')

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as client:
        response = await client.put(
            f'{base_url}{book.id}',
            json={'title': 'New Title'},
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Database error'}
    mock_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_update_book_deve_falhar_integrity_error_generico(
    authenticated_token: Token,
    user: User,
    book: Book,
):
    mock_session = Mock(spec=AsyncSession)
    mock_session.scalar.side_effect = [user, book]
    mock_session.commit.side_effect = IntegrityError(
        'statement', 'params', Exception('check constraint failed')
    )

    def mock_get_session():
        yield mock_session

    header_auth = {
        'Authorization': f'Bearer {authenticated_token.access_token}'
    }
    app.dependency_overrides[get_session] = mock_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as client:
        response = await client.put(
            f'{base_url}{book.id}',
            json={'title': 'New Title'},
            headers=header_auth,
        )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Database error'}
    mock_session.rollback.assert_called_once()


# ============================================================================
# DELETE TESTS
# ============================================================================
@pytest.mark.asyncio
async def test_delete_book_deve_ter_sucesso_e_retornar_mensagem(
    client: AsyncClient,
    authenticated_token: Token,
    session: AsyncSession,
    book: Book,
):
    response = await client.delete(
        f'{base_url}{book.id}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Book Removed'}


@pytest.mark.asyncio
async def test_delete_book_by_id_deve_falhar_e_retornar_exception(
    client: AsyncClient,
    authenticated_token: Token,
    book: Book,
):
    response = await client.delete(
        f'{base_url}{book.id + 999}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND

    assert response.json() == {'detail': 'Book not found'}


@pytest.mark.asyncio
async def test_delete_book_by_id_deve_falhar_com_rollback(
    client: AsyncClient,
    authenticated_token: Token,
    session: AsyncSession,
    book: Book,
):
    original_book_id = book.id

    with patch.object(
        session, 'commit', side_effect=SQLAlchemyError('DB Error')
    ):
        response = await client.delete(
            f'{base_url}{original_book_id}',
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    assert response.json() == {'detail': 'Database error'}

    session.expire_all()
    stmt = select(Book).where(Book.id == original_book_id)
    db_book = await session.scalar(stmt)
    assert db_book is not None
    assert db_book.id == original_book_id


# ============================================================================
# READ TESTS
# ============================================================================
@pytest.mark.asyncio
async def test_read_books_by_partial_name_deve_retornar_livros_filtrados(
    client: AsyncClient,
    novelist_with_books: Callable[
        [int, Optional[str], Optional[str]], Awaitable[Novelist]
    ],
):

    [
        await novelist_with_books(10, name_prefix=lang)  # type: ignore
        for lang in ('Python', 'Java', 'Rust')
    ]

    uri = f'{base_url}?' + urlencode({'name': 'Python'})
    response = await client.get(uri)

    assert response.status_code == HTTPStatus.OK
    data = response.json()

    assert data['total'] == 10  # noqa: PLR2004
    assert len(data['data']) == 10  # noqa: PLR2004
    assert all('Python' in book['name'] for book in data['data'])


@pytest.mark.asyncio
async def test_read_books_by_partial_title_deve_retornar_livros_filtrados(
    client: AsyncClient,
    session: AsyncSession,
    novelist_with_books: Callable[
        [int, Optional[str], Optional[str]], Awaitable[Novelist]
    ],
):
    await novelist_with_books(5, title_prefix='Advanced')  # type: ignore
    await novelist_with_books(5, title_prefix='Beginner')  # type: ignore

    uri = f'{base_url}?' + urlencode({'title': 'Advanced'})
    response = await client.get(uri)

    assert response.status_code == HTTPStatus.OK
    data = response.json()

    db_books = (await session.scalars(select(Book))).all()

    assert db_books
    assert data['total'] == 5  # noqa: PLR2004
    assert all('Advanced' in book['title'] for book in data['data'])


@pytest.mark.asyncio
async def test_read_books_by_year_range_deve_retornar_livros_filtrados(
    client: AsyncClient,
    session: AsyncSession,
    novelist: Novelist,
):
    # Cria livros com anos específicos
    books = [
        BookFactory.build(year=2019, id_novelist=novelist.id),
        BookFactory.build(year=2020, id_novelist=novelist.id),
        BookFactory.build(year=2021, id_novelist=novelist.id),
        BookFactory.build(year=2022, id_novelist=novelist.id),
        BookFactory.build(year=2023, id_novelist=novelist.id),
    ]
    session.add_all(books)
    await session.commit()

    # Filtro: yearFrom=2020, yearTo=2022 (exclusive)
    uri = f'{base_url}?' + urlencode({'yearFrom': 2020, 'yearTo': 2022})
    response = await client.get(uri)

    assert response.status_code == HTTPStatus.OK
    data = response.json()

    assert data['total'] == 2  # 2020 e 2021  # noqa: PLR2004
    years = [book['year'] for book in data['data']]
    assert 2020 in years  # noqa: PLR2004
    assert 2021 in years  # noqa: PLR2004
    assert 2022 not in years  # noqa: PLR2004


@pytest.mark.asyncio
async def test_read_books_com_multiplos_filtros_deve_retornar_correto(
    client: AsyncClient,
    session: AsyncSession,
    novelist: Novelist,
):
    books = [
        BookFactory.build(
            name='Python Basics', year=2020, id_novelist=novelist.id
        ),
        BookFactory.build(
            name='Python Advanced', year=2021, id_novelist=novelist.id
        ),
        BookFactory.build(
            name='Java Basics', year=2020, id_novelist=novelist.id
        ),
        BookFactory.build(
            name='Python Expert', year=2022, id_novelist=novelist.id
        ),
    ]
    session.add_all(books)
    await session.commit()

    # Filtro: name='Python' AND yearFrom=2021
    uri = f'{base_url}?' + urlencode({'name': 'Python', 'yearFrom': 2021})
    response = await client.get(uri)

    assert response.status_code == HTTPStatus.OK
    data = response.json()

    assert data['total'] == 2  # noqa: PLR2004  # Python Advanced (2021) e Python Expert (2022)
    assert all('Python' in book['name'] for book in data['data'])
    assert all(book['year'] >= 2021 for book in data['data'])  # noqa: PLR2004


@pytest.mark.asyncio
async def test_read_books_sem_filtros_deve_retornar_todos(
    client: AsyncClient,
    novelist_with_books: Callable[
        [int, Optional[str], Optional[str]], Awaitable[Novelist]
    ],
):
    await novelist_with_books(15, None, None)

    response = await client.get(base_url)

    assert response.status_code == HTTPStatus.OK
    data = response.json()

    assert data['total'] == 15  # noqa: PLR2004
    assert len(data['data']) == 10  # limite padrão   # noqa: PLR2004
    assert data['page'] == 1
    assert data['hasNext'] is True


@pytest.mark.asyncio
async def test_read_books_filtro_sem_resultado_deve_retornar_lista_vazia(
    client: AsyncClient,
    session: AsyncSession,
    novelist_with_books: Callable[
        [int, Optional[str], Optional[str]], Awaitable[Novelist]
    ],
):
    await novelist_with_books(5, name_prefix='Python')  # type: ignore

    uri = f'{base_url}?' + urlencode({'name': 'NonExistent'})
    response = await client.get(uri)

    assert response.status_code == HTTPStatus.OK
    data = response.json()

    assert data['total'] == 0
    assert data['data'] == []
    assert data['hasPrev'] is False
    assert data['hasNext'] is False


@pytest.mark.asyncio
async def test_read_books_paginacao_deve_funcionar_corretamente(
    client: AsyncClient,
    session: AsyncSession,
    novelist_with_books: Callable[
        [int, Optional[str], Optional[str]], Awaitable[Novelist]
    ],
):
    await novelist_with_books(25, 'Book', 'book_title')

    # Página 1
    uri1 = f'{base_url}?' + urlencode({'page': 1, 'limit': 10})
    response1 = await client.get(uri1)
    data1 = response1.json()

    assert data1['total'] == 25  # noqa: PLR2004
    assert len(data1['data']) == 10  # noqa: PLR2004
    assert data1['hasPrev'] is False
    assert data1['hasNext'] is True

    # Página 2
    uri2 = f'{base_url}?' + urlencode({'page': 2, 'limit': 10})
    response2 = await client.get(uri2)
    data2 = response2.json()

    assert len(data2['data']) == 10  # noqa: PLR2004
    assert data2['hasPrev'] is True
    assert data2['hasNext'] is True

    # Página 3 (última)
    uri3 = f'{base_url}?' + urlencode({'page': 3, 'limit': 10})
    response3 = await client.get(uri3)
    data3 = response3.json()

    assert len(data3['data']) == 5  # noqa: PLR2004
    assert data3['hasPrev'] is True
    assert data3['hasNext'] is False


@pytest.mark.asyncio
async def test_read_book_by_id_deve_ter_sucesso_e_retornar_book(
    client: AsyncClient,
    session: AsyncSession,
    book: Book,
):
    response = await client.get(f'{base_url}{book.id}')
    assert response.status_code == HTTPStatus.OK
    _book_schema = BookPublic.model_validate(book)
    assert response.json() == _book_schema.model_dump()


@pytest.mark.asyncio
async def test_read_book_by_id_deve_falhar_e_retornar_exception(
    client: AsyncClient,
    book: Book,
):
    response = await client.get(f'{base_url}{book.id + 999}')
    assert response.status_code == HTTPStatus.NOT_FOUND

    assert response.json() == {'detail': 'Book not found'}


@pytest.mark.asyncio
async def test_read_books_ordenacao_parametrizada(client, novelist_with_books):
    """Testa ordenação com diferentes combinações"""

    await novelist_with_books(30)

    for order_by in ['id', 'name', 'title', 'year']:
        for order_dir in ['asc', 'desc']:
            params = urlencode({
                'orderBy': order_by,
                'orderDir': order_dir,
                'limit': 5,
            })
            response = await client.get(f'/books/?{params}')

            assert response.status_code == HTTPStatus.OK
            data = response.json()

            if len(data['data']) > 1:
                sorted_data = sorted(
                    data['data'],
                    key=lambda x: x[order_by],
                    reverse=(order_dir == 'desc'),
                )
                assert data['data'] == sorted_data
