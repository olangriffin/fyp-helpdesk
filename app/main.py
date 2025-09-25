from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401 -- ensure models are registered with SQLAlchemy metadata
from app.api import api_router
from app.core.config import get_settings
from app.core.database import Base, engine

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(api_router)
