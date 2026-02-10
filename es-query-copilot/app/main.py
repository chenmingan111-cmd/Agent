from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import settings
from app.services.es_client import es_client
from app.api import draft, validate, run, explain, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting ES Query Copilot...")
    yield
    # Shutdown
    print("Shutting down...")
    await es_client.close()

app = FastAPI(
    title="ES Query Copilot",
    version="1.0.0",
    lifespan=lifespan
)

# Register Routers
app.include_router(draft.router, tags=["Draft"])
app.include_router(validate.router, tags=["Validate"])
app.include_router(run.router, tags=["Run"])
app.include_router(explain.router, tags=["Explain"])
app.include_router(health.router, tags=["Health"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
