import os

import pytest


def pytest_sessionstart(session: pytest.Session) -> None:
    """Protect local runtime data from destructive integration-test setup.

    Integration tests intentionally truncate funding tables. CI uses an ephemeral
    PostgreSQL service and explicitly opts into database reuse. Local development
    must use a distinct TEST_DATABASE_URL when DATABASE_URL is also configured.
    """

    database_url = os.getenv("DATABASE_URL")
    test_database_url = os.getenv("TEST_DATABASE_URL")
    allow_reuse = os.getenv("ALLOW_TEST_DATABASE_REUSE", "").casefold() in {
        "1",
        "true",
        "yes",
    }

    if (
        database_url
        and test_database_url
        and database_url == test_database_url
        and not allow_reuse
    ):
        raise pytest.UsageError(
            "Refusing to run tests because TEST_DATABASE_URL equals DATABASE_URL. "
            "Integration tests truncate database tables. Use a separate test database, "
            "or set ALLOW_TEST_DATABASE_REUSE=true only for an explicitly ephemeral database."
        )
