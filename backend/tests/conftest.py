import pytest

from app.application import disruptions
from app.application.disruption_collector import seed_from_exports
from app.infra.disruption_store import Store


@pytest.fixture(scope="session", autouse=True)
def seeded_store(tmp_path_factory):
    """Session database seeded offline from the committed data/analysis exports."""
    store = Store(tmp_path_factory.mktemp("db") / "disruptions.sqlite")
    assert seed_from_exports(store, disruptions.ANALYSIS)
    disruptions.use_store(store)
    yield store
