from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from psycopg import Connection


def create_ingestion(
    connection: Connection,
    load_id: UUID,
    filename: str,
) -> None:

    connection.execute(
        """
        INSERT INTO ingestions (
            id,
            filename,
            row_count
        )
        VALUES (%s, %s, %s)
        """,
        (load_id, filename, 0),
    )

def insert_constituents(
    connection: Connection,
    rows: list[dict],
) -> None:

    query = """
        INSERT INTO constituents (
            ingestion_id,
            index_code,
            isin,
            ticker,
            name,
            weight,
            shares,
            effective_date
        )
        VALUES (
            %(ingestion_id)s,
            %(index_code)s,
            %(isin)s,
            %(ticker)s,
            %(name)s,
            %(weight)s,
            %(shares)s,
            %(effective_date)s
        )
    """

    with connection.cursor() as cursor:
        cursor.executemany(
            query,
            rows,
        )

def update_ingestion_count(
    connection: Connection,
    load_id: UUID,
    row_count: int,
) -> None:

    connection.execute(
        """
        UPDATE ingestions
        SET row_count = %s
        WHERE id = %s
        """,
        (row_count, load_id),
    )


def logically_delete(
    connection: Connection,
    constituent_id: int,
) -> datetime | None:

    row = connection.execute(
        """
        UPDATE constituents
        SET deleted_at = CURRENT_TIMESTAMP
        WHERE id = %s
          AND deleted_at IS NULL
        RETURNING id, deleted_at
        """,
        (constituent_id,),
    ).fetchone()

    if row is None:
        return None

    return row[1]

def get_current_constituents(
    connection: Connection,
    start_date: date,
    end_date: date,
):
    query = """
        SELECT DISTINCT ON (
            c.index_code,
            c.isin,
            c.effective_date
        )
            c.id,
            c.index_code,
            c.isin,
            c.ticker,
            c.name,
            c.weight,
            c.shares,
            c.effective_date

        FROM constituents c

        INNER JOIN ingestions i
            ON i.id = c.ingestion_id

        WHERE c.effective_date >= %s
          AND c.effective_date <= %s
          AND c.deleted_at IS NULL

        ORDER BY
            c.index_code,
            c.isin,
            c.effective_date,
            i.loaded_at DESC,
            c.id DESC
    """

    return connection.execute(
        query,
        (start_date, end_date),
    ).fetchall()