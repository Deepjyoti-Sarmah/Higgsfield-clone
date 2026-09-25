import uuid
from datetime import UTC, datetime

from fastapi import FastAPI
from httpx import AsyncClient

from app.schemas.share import PublicJobResponse
from app.schemas.uploads import UploadCreateRequest

NEW_PATHS = {
    "/api/v1/sequence-jobs",
    "/api/v1/sequence-jobs/{job_id}",
    "/api/v1/credits/ledger",
}


def build_clip_payload(count: int, transition: str = "cut") -> dict:
    return {
        "clips": [
            {"job_id": str(uuid.uuid4()), "transition_in": transition} for _ in range(count)
        ],
        "idempotency_key": "test-key-123",
    }


def test_new_paths_exist_in_openapi(app: FastAPI) -> None:
    assert NEW_PATHS <= set(app.openapi()["paths"])


async def test_create_rejects_one_clip(guest_client: AsyncClient) -> None:
    response = await guest_client.post("/api/v1/sequence-jobs", json=build_clip_payload(1))

    assert response.status_code == 422


async def test_create_rejects_seven_clips(guest_client: AsyncClient) -> None:
    response = await guest_client.post("/api/v1/sequence-jobs", json=build_clip_payload(7))

    assert response.status_code == 422


async def test_create_rejects_unknown_transition(guest_client: AsyncClient) -> None:
    response = await guest_client.post(
        "/api/v1/sequence-jobs", json=build_clip_payload(2, transition="dissolve")
    )

    assert response.status_code == 422


async def test_ledger_rejects_zero_limit(guest_client: AsyncClient) -> None:
    response = await guest_client.get("/api/v1/credits/ledger", params={"limit": 0})

    assert response.status_code == 422


def test_upload_accepts_audio_mpeg() -> None:
    body = UploadCreateRequest(content_type="audio/mpeg", byte_size=1024)

    assert body.content_type == "audio/mpeg"


def test_share_defaults_kind_to_video() -> None:
    view = PublicJobResponse(
        id=uuid.uuid4(),
        status="queued",
        preset_slug=None,
        preset_name=None,
        poster_url=None,
        video_url=None,
        created_at=datetime.now(UTC),
    )

    assert view.kind == "video"
