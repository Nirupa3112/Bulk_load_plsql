from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class UploadResponse(BaseModel):
    load_id: UUID
    filename: str
    rows_loaded: int
    status: str


class DeleteResponse(BaseModel):
    id: int
    status: str
    deleted_at: datetime


class ConstituentResponse(BaseModel):
    id: int
    index_code: str
    isin: str
    ticker: str
    name: str
    weight: Decimal
    shares: Decimal
    effective_date: date