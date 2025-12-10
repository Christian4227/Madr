from datetime import datetime

from pydantic import BaseModel


class DateSchema(BaseModel):
    created_at: datetime
    updated_at: datetime
