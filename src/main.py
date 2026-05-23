from dotenv import load_dotenv
from fastapi import FastAPI

from src.presentation.routers import create_catalog_router

load_dotenv()


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/")
    async def read_root() -> dict[str, str]:
        return {"message": "API online"}

    app.include_router(create_catalog_router())
    return app


app = create_app()
