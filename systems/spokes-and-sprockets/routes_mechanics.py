# routes_mechanics.py - the mechanics. Theo H.
from fastapi import APIRouter

import services

router = APIRouter()


@router.get("/api/mechanics")
def mechanics():
    """The mechanics and how many hours of jobs each can take on per week (Mon-Sat)."""
    return services.list_mechanics()
