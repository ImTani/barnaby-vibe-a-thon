# routes_money.py - invoices and takings. Theo H.
from fastapi import APIRouter
from pydantic import BaseModel

import services
from db import today

router = APIRouter()


class InvoiceIn(BaseModel):
    job_id: int
    amount: float


@router.get("/api/invoices/unpaid")
def unpaid():
    """Invoices customers haven't paid yet."""
    return services.unpaid_invoices()


@router.post("/api/invoices")
def create_invoice(body: InvoiceIn):
    """Raise an invoice for a finished job (amount in pounds)."""
    return services.create_invoice(body.job_id, body.amount)
