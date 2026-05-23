import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///banco_teste.db")


def _resolve_sync_url() -> str:
    url = DATABASE_URL
    if "+" in url:
        url = "sqlite:///" + url.split("///", 1)[1]
    return url


sync_engine = create_engine(_resolve_sync_url(), echo=False)
SyncSessionFactory = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
)
