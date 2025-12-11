from datetime import datetime

import factory
from factory import fuzzy

from madr.models.book import Book
from madr.models.novelist import Novelist
from madr.models.user import User


class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'test_name_{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    password = factory.Sequence(
        lambda n: f'test_pwd_{n}'
    )


class NovelistFactory(factory.Factory):
    class Meta:
        model = Novelist

    name = factory.Sequence(lambda n: f'novelist_name_{n}')


class BookFactory(factory.Factory):
    class Meta:
        model = Book

    name = factory.Sequence(lambda n: f'book_name_{n}')
    year = factory.LazyFunction(
        lambda: str(fuzzy.FuzzyInteger(1560, datetime.now().year).fuzz())
    )
    title = factory.Sequence(lambda n: f'book_title_{n}')
    id_novelist = factory.SelfAttribute('novelist.id')
    novelist = factory.SubFactory(NovelistFactory)
