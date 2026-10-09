"""SQL guard tests focus on dangerous inputs."""
import pytest

from app.guards import validate_select


def test_select_gets_row_limit() -> None:
    assert validate_select("SELECT id FROM orders") == "SELECT id FROM orders LIMIT 100"


@pytest.mark.parametrize("sql", ["DELETE FROM orders", "SELECT 1; DROP TABLE orders", "SELECT 1 -- hi", "SELECT pg_sleep(20)"])
def test_rejects_unsafe_sql(sql: str) -> None:
    with pytest.raises(ValueError):
        validate_select(sql)


def test_replaces_large_requested_limit() -> None:
    assert validate_select("SELECT * FROM orders LIMIT 999999").endswith("LIMIT 100")
