import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from fastapi import UploadFile
from psycopg import Connection

from app.repositories.constituent_repository import (
    create_ingestion,
    insert_constituents,
    update_ingestion_count,
)


REQUIRED_COLUMNS = {
    "index_code",
    "isin",
    "ticker",
    "name",
    "weight",
    "shares",
    "effective_date",
}

BATCH_SIZE = 1000


def parse_date(
    value: str,
    row_number: int,
) -> date:

    try:
        return date.fromisoformat(
            value.strip()
        )

    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: "
            f"invalid effective_date '{value}'"
        ) from exc


def parse_decimal(
    value: str,
    field_name: str,
    row_number: int,
) -> Decimal:

    try:
        return Decimal(value.strip())

    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(
            f"Row {row_number}: "
            f"invalid {field_name} '{value}'"
        ) from exc

def ingest_csv(
    connection: Connection,
    file: UploadFile,
) -> tuple[UUID, int]:

    load_id = uuid4()

    filename = file.filename or "upload.csv"

    create_ingestion(
        connection,
        load_id,
        filename,
    )

    total_rows = 0
    batch = []

    text_stream = None

    try:
        import io

        text_stream = io.TextIOWrapper(
            file.file,
            encoding="utf-8-sig",
            newline="",
        )

        reader = csv.DictReader(text_stream)

        if not reader.fieldnames:
            raise ValueError(
                "CSV file has no header"
            )

        actual_columns = set(
            reader.fieldnames
        )

        missing_columns = (
            REQUIRED_COLUMNS - actual_columns
        )

        if missing_columns:
            raise ValueError(
                "Missing required columns: "
                f"{sorted(missing_columns)}"
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):

            if not any(
                value and value.strip()
                for value in row.values()
            ):
                continue

            index_code = (
                row["index_code"] or ""
            ).strip()

            isin = (
                row["isin"] or ""
            ).strip()

            ticker = (
                row["ticker"] or ""
            ).strip()

            name = (
                row["name"] or ""
            ).strip()

            if not index_code:
                raise ValueError(
                    f"Row {row_number}: "
                    "index_code is required"
                )

            if not isin:
                raise ValueError(
                    f"Row {row_number}: "
                    "isin is required"
                )

            batch.append(
                {
                    "ingestion_id": load_id,
                    "index_code": index_code,
                    "isin": isin,
                    "ticker": ticker,
                    "name": name,
                    "weight": parse_decimal(
                        row["weight"],
                        "weight",
                        row_number,
                    ),
                    "shares": parse_decimal(
                        row["shares"],
                        "shares",
                        row_number,
                    ),
                    "effective_date": parse_date(
                        row["effective_date"],
                        row_number,
                    ),
                }
            )

            total_rows += 1

            if len(batch) >= BATCH_SIZE:
                insert_constituents(
                    connection,
                    batch,
                )

                batch.clear()

        if batch:
            insert_constituents(
                connection,
                batch,
            )

        update_ingestion_count(
            connection,
            load_id,
            total_rows,
        )

        return load_id, total_rows

    except Exception:
        raise