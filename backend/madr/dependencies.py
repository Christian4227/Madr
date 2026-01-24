from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordRequestForm

from madr.core.security import get_current_user
from madr.schemas.books import BookQueryParams
from madr.schemas.novelists import NovelistQueryParams
from madr.schemas.user import AuthContext

ActiveUser = Annotated[AuthContext, Depends(get_current_user)]
RequestFormData = Annotated[OAuth2PasswordRequestForm, Depends()]


BookQuery = Annotated[BookQueryParams, Query()]
NovelistQuery = Annotated[NovelistQueryParams, Query()]

AnnotatedBookQueryParams = Annotated[BookQueryParams, Query()]
AnnotatedNovelistQueryParams = Annotated[NovelistQueryParams, Query()]
