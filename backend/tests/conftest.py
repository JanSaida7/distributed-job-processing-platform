import os
import sys
from pathlib import Path

import pytest


backend_directory = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_directory))

# Tests must never use a developer's PostgreSQL database or dispatch real jobs.
# This is set before application modules load their cached settings.
os.environ["DATABASE_URL"] = "sqlite+pysqlite://"
os.environ["ENABLE_JOB_QUEUE"] = "false"
os.environ["SECRET_KEY"] = "test-only-secret-key"

from app.db.base import Base
from app.db import models  # noqa: F401 - registers model metadata
from app.db.session import SessionLocal, engine


@pytest.fixture(scope="session", autouse=True)
def test_database() -> None:
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clear_test_database() -> None:
    database = SessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            database.execute(table.delete())
        database.commit()
    finally:
        database.close()
