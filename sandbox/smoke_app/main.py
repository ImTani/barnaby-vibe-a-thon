"""Tiny FastAPI app for the Phase 0 Synapse smoke test.

Each route probes one known Synapse 0.1.9 pitfall, so the generated server tells us what really happens:
  GET  /items             plain list                                -> should work
  GET  /items/{item_id}   path parameter                            -> should work
  GET  /search?q=         query parameter                           -> reported: dropped in local Auto mode
  POST /orders            Pydantic body in the same file, with a
                          Literal field and a trailing-comment field -> reported: those two fields dropped
  GET  /v2/ping           router with prefix="/v2"                  -> reported: prefix dropped (tool calls /ping)
  GET  /fail              always 409 with a JSON body               -> reported: error body hidden by raise_for_status
"""
from typing import Literal

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Smoke shop")

ITEMS = {
    1: {"id": 1, "name": "Brake pads", "stock": 3},
    2: {"id": 2, "name": "Inner tube", "stock": 0},
}


@app.get("/items")
def list_items():
    """List every item with its stock level."""
    return list(ITEMS.values())


@app.get("/items/{item_id}")
def get_item(item_id: int):
    """Get one item by its id."""
    if item_id not in ITEMS:
        raise HTTPException(status_code=404, detail=f"No item {item_id}")
    return ITEMS[item_id]


@app.get("/search")
def search(q: str):
    """Search items whose name contains q."""
    return [i for i in ITEMS.values() if q.lower() in i["name"].lower()]


class OrderIn(BaseModel):
    item_id: int
    quantity: int
    supplier: str
    priority: Literal["normal", "rush"] = "normal"
    note: str = ""  # free-text note for the supplier


@app.post("/orders")
def create_order(order: OrderIn):
    """Create a purchase order for an item and echo back what the server received."""
    return {"created": True, "received": order.model_dump()}


@app.get("/fail")
def fail():
    """Always refuses, with a reason in the body."""
    raise HTTPException(status_code=409, detail="Only 3 units available")


router = APIRouter(prefix="/v2")


@router.get("/ping")
def ping():
    """Health check on a prefixed router."""
    return {"ok": True}


app.include_router(router)
