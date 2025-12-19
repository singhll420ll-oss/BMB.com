"""
Routers package initialization
"""

from routers.auth import router as auth_router
from routers.customer import router as customer_router
from routers.admin import router as admin_router
from routers.team_member import router as team_member_router
from routers.services import router as services_router
from routers.orders import router as orders_router

__all__ = [
    "auth_router",
    "customer_router",
    "admin_router",
    "team_member_router",
    "services_router",
    "orders_router",
]