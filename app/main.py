from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routers.camera import router as camera_router
from .routers.stats import router as stats_router
from .routers.stepper import router as stepper_router
from .routers.webrtc import router as webrtc_router
from .routers.valve import router as valve_router

# Load environment variables from .env file
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")


def create_app() -> FastAPI:
    app = FastAPI(title="UU Plastination Secure API", docs_url=None, redoc_url=None)
    
    # Mount routers
    app.include_router(stats_router)
    app.include_router(stepper_router)
    app.include_router(camera_router)
    app.include_router(webrtc_router)
    app.include_router(valve_router)
    
    # Get the project root directory (parent of app/)
    project_root = Path(__file__).parent.parent
    
    # Mount static files (assets)
    assets_path = project_root / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
    
    # Serve index.html at root
    @app.get("/")
    def serve_index():
        index_path = project_root / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"message": "Dashboard not found"}
    
    # Placeholder logout endpoint
    @app.get("/logout")
    def logout():
        return {"message": "Logout endpoint - implement authentication as needed"}
    
    return app


app = create_app()
