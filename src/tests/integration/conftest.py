from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.db.base import Base
from src.infrastructure.db.session import SyncSessionFactory


@pytest.fixture(autouse=True)
def _setup_test_db() -> Generator[None, None, None]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    test_session_factory = sessionmaker(
        bind=engine, class_=Session, expire_on_commit=False
    )

    Base.metadata.create_all(bind=engine)

    original_factory = SyncSessionFactory
    import src.infrastructure.db.session as session_module

    session_module.SyncSessionFactory = test_session_factory

    yield

    session_module.SyncSessionFactory = original_factory
    Base.metadata.drop_all(bind=engine)
