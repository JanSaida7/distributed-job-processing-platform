from sqlalchemy import inspect

from app.db.base import Base
from app.db.models import Job, User
from app.db.session import engine


def test_expected_database_tables_are_defined() -> None:
    table_names = {table.name for table in Base.metadata.sorted_tables}

    assert "users" in table_names
    assert "jobs" in table_names
    assert "status" in {column.name for column in Job.__table__.columns}
    assert "email" in {column.name for column in User.__table__.columns}


def test_database_has_expected_tables() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    assert "users" in table_names
    assert "jobs" in table_names
