from contextlib import contextmanager
from typing import Iterator

from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import settings

pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row},
    open=False,
)


@contextmanager
def get_connection() -> Iterator[Connection]:
    with pool.connection() as connection:
        yield connection
