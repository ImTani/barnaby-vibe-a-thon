# routes_parts.py - parts, stock and ordering from suppliers. Theo H, 2011.
from fastapi import APIRouter
from pydantic import BaseModel

import services

router = APIRouter()


class AdjustIn(BaseModel):
    change: int
    reason: str | None = None


class PurchaseOrderIn(BaseModel):
    part_id: int
    quantity: int
    supplier: str | None = None


@router.get("/api/parts")
def parts():
    """Every part we stock: SKU, name, how many are in stock, reorder level, usual supplier and unit cost."""
    return services.list_parts()


@router.get("/api/parts/low")
def parts_low():
    """Parts at or below their reorder level (time to order more)."""
    return services.low_stock_parts()


@router.post("/api/parts/{part_id}/adjust")
def adjust(part_id: int, body: AdjustIn):
    """Add (positive change) or remove (negative change) stock for a part, with a reason."""
    return services.adjust_stock(part_id, body.change, body.reason or "")


@router.get("/api/purchase-orders")
def purchase_orders():
    """All purchase orders to suppliers, newest first."""
    return services.list_purchase_orders()


@router.post("/api/purchase-orders")
def create_purchase_order(body: PurchaseOrderIn):
    """Order more of a part from a supplier. supplier defaults to the part's usual one."""
    return services.create_purchase_order(body.part_id, body.quantity, body.supplier or "")


@router.post("/api/purchase-orders/{po_id}/receive")
def receive(po_id: int):
    """Mark a purchase order as delivered and add the parts to stock."""
    return services.receive_purchase_order(po_id)
