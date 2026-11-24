# routes_customers.py - customers + texting them. Theo H.
from fastapi import APIRouter
from pydantic import BaseModel

import services

router = APIRouter()


class CustomerIn(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None


class NotifyIn(BaseModel):
    message: str
    channel: str | None = None
    job_id: int | None = None


@router.get("/api/customers/search/{name}")
def search(name: str):
    """Find customers whose name contains the given text."""
    return services.search_customers(name)


@router.get("/api/customers/{customer_id}")
def customer_detail(customer_id: int):
    """One customer: contact details, last visit, their bikes and recent jobs."""
    return services.get_customer(customer_id)


@router.post("/api/customers")
def add_customer(body: CustomerIn):
    """Add a new customer."""
    return services.add_customer(body.name, body.phone or "", body.email or "")


@router.post("/api/customers/{customer_id}/notify")
def notify(customer_id: int, body: NotifyIn):
    """Text (channel sms, the default) or email a customer, e.g. to say their bike is ready."""
    return services.notify_customer(customer_id, body.message, body.channel or "sms", body.job_id)


@router.get("/api/notifications/recent")
def recent_notifications():
    """The last texts and emails the shop sent to customers."""
    return services.recent_notifications()
