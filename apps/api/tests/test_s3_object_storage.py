import uuid
from pathlib import Path

import httpx
import pytest

from app.adapters.object_storage import build_asset_url
from app.adapters.s3_object_storage import S3ObjectStorage
from app.settings import Settings
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage

CONTENT_TYPE = "image/jpeg"
PAYLOAD = b"\xff\xd8\xff\xe0not-a-real-jpeg"
TTL_SECONDS = 900


@pytest.fixture
def storage() -> S3ObjectStorage:
    return S3ObjectStorage(Settings())


async def test_presigned_put_then_read_download_delete(storage: S3ObjectStorage, tmp_path: Path) -> None:
    key = f"tests/{uuid.uuid4().hex}.jpg"
    upload_url = storage.create_upload_url(key, CONTENT_TYPE, TTL_SECONDS)

    async with httpx.AsyncClient() as http_client:
        uploaded = await http_client.put(
            upload_url, content=PAYLOAD, headers={"Content-Type": CONTENT_TYPE}
        )
    assert uploaded.status_code == 200
    assert await storage.read_object_size(key) == len(PAYLOAD)

    downloaded = tmp_path / "downloaded.jpg"
    await storage.download_to_path(key, downloaded)
    assert downloaded.read_bytes() == PAYLOAD

    await storage.delete_object(key)
    assert await storage.read_object_size(key) is None


async def test_presigned_put_rejects_a_different_content_type(storage: S3ObjectStorage) -> None:
    key = f"tests/{uuid.uuid4().hex}.jpg"
    upload_url = storage.create_upload_url(key, CONTENT_TYPE, TTL_SECONDS)

    async with httpx.AsyncClient() as http_client:
        rejected = await http_client.put(
            upload_url, content=PAYLOAD, headers={"Content-Type": "text/plain"}
        )

    assert rejected.status_code == 403


def test_build_asset_url_prefers_the_public_base_url() -> None:
    storage = InMemoryObjectStorage()

    public = build_asset_url(storage, "users/1/a.jpg", "https://cdn.example.com/", 60)
    signed = build_asset_url(storage, "users/1/a.jpg", "", 60)

    assert public == "https://cdn.example.com/users/1/a.jpg"
    assert signed == "memory://users/1/a.jpg?get"
