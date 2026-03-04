import pytest
from google.cloud import datastore
from testcontainers.google import DatastoreContainer


@pytest.mark.integration
def test_datastore_container_roundtrip() -> None:
    with DatastoreContainer() as datastore_container:
        datastore_client = datastore_container.get_datastore_client()

        key = datastore_client.key("notes_test_kind", "notes_test_id")
        entity = datastore.Entity(key=key)
        entity.update({"value": "ok"})

        datastore_client.put(entity)
        fetched = datastore_client.get(key)

    assert fetched is not None
    assert fetched["value"] == "ok"