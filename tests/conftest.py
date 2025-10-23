import pytest
import pytest_asyncio
import asyncio
import os


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def cleanup_test_files():
    yield
    test_files = ["test_dedup.db", "test_init.db"]
    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
            except:
                pass
