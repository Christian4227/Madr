from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

from freezegun import freeze_time


@contextmanager
def frozen_context(time_delta: Optional[timedelta] = None):

    initial_datetime = datetime.now(tz=timezone.utc)  # trava no agora
    if time_delta:
        initial_datetime += time_delta
    with freeze_time(initial_datetime) as frozen_time:
        yield frozen_time
