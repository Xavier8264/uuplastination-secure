from fastapi import FastAPI

from .routers.stats import router as stats_router
from .routers.stepper import router as stepper_router


def create_app() -> FastAPI:
    app = FastAPI(title="UU Plastination Secure API", docs_url=None, redoc_url=None)
    # Mount stats router under /api
    app.include_router(stats_router)
    app.include_router(stepper_router)
    return app


app = create_app()
