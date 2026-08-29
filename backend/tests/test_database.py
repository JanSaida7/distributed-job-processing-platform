from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine


def test_database_url_targets_postgresql_database() -> None:
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.database_url.endswith("/job_processing")


def test_database_connection() -> None:
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1