import csv
import io
from datetime import date, datetime, timezone

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Query,
    UploadFile,
)

from app.database import get_connection
from app.repositories.constituent_repository import (
    get_current_constituents,
    logically_delete,
)
from app.schemas import (
    DeleteResponse,
    UploadResponse,
)
from app.services.ingestion import ingest_csv


router = APIRouter()

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=201,
)
def upload_csv(
    file: UploadFile = File(...),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are accepted",
        )

    try:
        with get_connection() as connection:

            load_id, row_count = ingest_csv(
                connection,
                file,
            )

            connection.commit()

            return UploadResponse(
                load_id=load_id,
                filename=file.filename,
                rows_loaded=row_count,
                status="success",
            )

    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail="CSV must be UTF-8 encoded",
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    # except Exception as exc:
    #     raise HTTPException(
    #         status_code=500,
    #         detail="Failed to ingest CSV",
    #     ) from exc
    except Exception as exc:
        print(f"CSV ingestion error: {type(exc).__name__}: {exc}")

        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest CSV: {exc}",
        ) from exc

@router.delete(
    "/constituents/{constituent_id}",
    response_model=DeleteResponse,
)
def delete_constituent(
    constituent_id: int,
):

    try:
        with get_connection() as connection:

            deleted_at = logically_delete(
                connection,
                constituent_id,
            )

            if deleted_at is None:
                connection.rollback()

                raise HTTPException(
                    status_code=404,
                    detail="Constituent not found",
                )

            connection.commit()

            return DeleteResponse(
                id=constituent_id,
                status="deleted",
                deleted_at=deleted_at,
            )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete constituent",
        ) from exc

@router.get("/export")
def export_data(
    start_date: date = Query(...),
    end_date: date = Query(...),
    format: str = Query(
        "json",
        pattern="^(json|csv)$",
    ),
):

    if start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail=(
                "start_date must be less than "
                "or equal to end_date"
            ),
        )

    try:
        with get_connection() as connection:

            rows = get_current_constituents(
                connection,
                start_date,
                end_date,
            )

        if format == "json":

            return [
                {
                    "id": row[0],
                    "index_code": row[1],
                    "isin": row[2],
                    "ticker": row[3],
                    "name": row[4],
                    "weight": str(row[5]),
                    "shares": str(row[6]),
                    "effective_date": (
                        row[7].isoformat()
                    ),
                }
                for row in rows
            ]

        output = io.StringIO()

        writer = csv.writer(output)

        writer.writerow(
            [
                "id",
                "index_code",
                "isin",
                "ticker",
                "name",
                "weight",
                "shares",
                "effective_date",
            ]
        )

        for row in rows:
            writer.writerow(row)

        output.seek(0)

        from fastapi.responses import StreamingResponse

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    "attachment; "
                    "filename=export.csv"
            },
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to export data",
        ) from exc

