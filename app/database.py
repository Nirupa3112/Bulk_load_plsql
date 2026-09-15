from contextlib import contextmanager
from pathlib import Path
from psycopg_pool import ConnectionPool
from app.config import settings


pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=settings.db_min_connections,
    max_size=settings.db_max_connections,
    open=False,
)


@contextmanager
def get_connection():
    with pool.connection() as connection:
        yield connection


def initialize_database():
    schema_path = Path(__file__).with_name(
        "database_schema.sql"
    )

    schema_sql = schema_path.read_text(
        encoding="utf-8"
    )

    with pool.connection() as connection:
        connection.execute(schema_sql)
        connection.commit()