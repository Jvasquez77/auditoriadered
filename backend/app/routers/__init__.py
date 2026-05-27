from app.routers.olts import router as olts_router
from app.routers.olt_ports import router as olt_ports_router
from app.routers.n1_infrastructure import router as n1_router
from app.routers.n2_infrastructure import router as n2_router
from app.routers.measurements import router as measurements_router
from app.routers.reports import router as reports_router

__all__ = [
    "olts_router",
    "olt_ports_router",
    "n1_router",
    "n2_router",
    "measurements_router",
    "reports_router",
]
