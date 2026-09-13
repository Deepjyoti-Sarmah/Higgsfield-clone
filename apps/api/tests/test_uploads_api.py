from httpx import AsyncClient

from app.schemas.uploads import MAX_UPLOAD_BYTES
from app.services.uploads import MAX_UPLOAD_BYTES as SERVICE_MAX_UPLOAD_BYTES
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage

JPEG_BYTES = b"\xff\xd8\xff" + b"0" * 300


def build_key(user_id: str, asset_id: str, extension: str = "jpg") -> str:
    return f"users/{user_id}/inputs/{asset_id}.{extension}"


async def current_user_id(client: AsyncClient) -> str:
    me = await client.get("/api/v1/me")
    assert me.status_code == 200
    return str(me.json()["id"])


async def open_upload(client: AsyncClient, byte_size: int = len(JPEG_BYTES)) -> dict[str, str]:
    created = await client.post(
        "/api/v1/uploads", json={"content_type": "image/jpeg", "byte_size": byte_size}
    )
    assert created.status_code == 201
    return created.json()


async def put_stored_object(
    client: AsyncClient, storage: InMemoryObjectStorage, upload: dict[str, str], content: bytes
) -> str:
    key = build_key(await current_user_id(client), upload["asset_id"])
    storage.put_bytes(key, content)
    return key


async def test_upload_without_cookie_is_unauthorized(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/uploads", json={"content_type": "image/jpeg", "byte_size": 100}
    )

    assert response.status_code == 401


async def test_allowed_image_types_create_a_presigned_put(guest_client: AsyncClient) -> None:
    for content_type, extension in (
        ("image/jpeg", "jpg"),
        ("image/png", "png"),
        ("image/webp", "webp"),
    ):
        response = await guest_client.post(
            "/api/v1/uploads", json={"content_type": content_type, "byte_size": 100}
        )

        assert response.status_code == 201
        body = response.json()
        assert body["upload_method"] == "PUT"
        assert body["upload_headers"] == {"Content-Type": content_type}
        assert body["asset_id"]
        assert body["expires_at"]
        assert body["upload_url"].endswith(f"/inputs/{body['asset_id']}.{extension}")


async def test_gif_and_oversized_uploads_are_rejected(guest_client: AsyncClient) -> None:
    gif = await guest_client.post(
        "/api/v1/uploads", json={"content_type": "image/gif", "byte_size": 100}
    )
    oversized = await guest_client.post(
        "/api/v1/uploads",
        json={"content_type": "image/png", "byte_size": MAX_UPLOAD_BYTES + 1},
    )

    assert gif.status_code == 422
    assert oversized.status_code == 422


async def test_complete_before_the_put_conflicts(guest_client: AsyncClient) -> None:
    upload = await open_upload(guest_client)

    response = await guest_client.post(f"/api/v1/uploads/{upload['asset_id']}/complete")

    assert response.status_code == 409
    assert response.json()["detail"] == "Upload not found in storage"


async def test_complete_is_idempotent_and_returns_a_download_url(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    upload = await open_upload(guest_client)
    await put_stored_object(guest_client, object_storage, upload, JPEG_BYTES)

    first = await guest_client.post(f"/api/v1/uploads/{upload['asset_id']}/complete")
    second = await guest_client.post(f"/api/v1/uploads/{upload['asset_id']}/complete")

    assert first.status_code == 200
    assert second.status_code == 200
    body = first.json()
    assert body["status"] == "ready"
    assert body["kind"] == "input_image"
    assert body["byte_size"] == len(JPEG_BYTES)
    assert body["url"]
    assert second.json()["url"] == body["url"]


async def test_complete_with_a_declared_size_mismatch_deletes_the_object(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    upload = await open_upload(guest_client, byte_size=len(JPEG_BYTES) + 10)
    key = await put_stored_object(guest_client, object_storage, upload, JPEG_BYTES)

    response = await guest_client.post(f"/api/v1/uploads/{upload['asset_id']}/complete")

    assert response.status_code == 422
    assert response.json()["detail"] == "Uploaded file does not match the declared size"
    assert await object_storage.read_object_size(key) is None


async def test_complete_with_an_oversized_object_is_rejected(
    guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    upload = await open_upload(guest_client, byte_size=MAX_UPLOAD_BYTES)
    key = await put_stored_object(guest_client, object_storage, upload, b"x" * (MAX_UPLOAD_BYTES + 1))

    response = await guest_client.post(f"/api/v1/uploads/{upload['asset_id']}/complete")

    assert response.status_code == 422
    assert await object_storage.read_object_size(key) is None


async def test_another_guest_cannot_complete_the_upload(
    guest_client: AsyncClient, other_guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    upload = await open_upload(guest_client)
    await put_stored_object(guest_client, object_storage, upload, JPEG_BYTES)

    response = await other_guest_client.post(f"/api/v1/uploads/{upload['asset_id']}/complete")

    assert response.status_code == 404


def test_upload_limit_matches_the_schema() -> None:
    assert SERVICE_MAX_UPLOAD_BYTES == MAX_UPLOAD_BYTES
