import asyncio
from typing import Any

from httpx import AsyncClient

from app.adapters.modal_adapter import ModalAdapter
from app.adapters.modal_image_adapter import ModalImageAdapter
from app.settings import Settings, get_settings
from app.storage_dependencies import get_object_storage
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import create_queued_job


class _FailingStorage(InMemoryObjectStorage):
    async def read_object_size(self, key: str) -> int | None:
        raise OSError("minio is gone")


class _FakeWriter:
    def close(self) -> None:
        return None

    async def wait_closed(self) -> None:
        return None


def _override_settings(app: Any, **fields: Any) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(**fields)


async def _deep(client: AsyncClient) -> dict[str, Any]:
    response = await client.get("/api/health/deep")
    return {"http": response.status_code, **response.json()}


async def test_deep_reports_all_five_checks(app: Any, guest_client: AsyncClient) -> None:
    _override_settings(app, generation_backend="local-motion")
    body = await _deep(guest_client)
    assert body["http"] == 200
    assert body["status"] == "ok"
    assert set(body["checks"]) == {"database", "storage", "video_backend", "image_backend", "queue"}
    for check in body["checks"].values():
        assert check["status"] in ("ok", "degraded", "down")
        assert isinstance(check["duration_ms"], int)
    assert body["checks"]["video_backend"]["detail"] == "local-motion"
    assert body["checks"]["queue"]["detail"]["depth"] >= 0


async def test_storage_down_gives_503(app: Any, guest_client: AsyncClient,
                                      object_storage: InMemoryObjectStorage) -> None:
    app.dependency_overrides[get_object_storage] = lambda: _FailingStorage()
    _override_settings(app, generation_backend="local-motion")
    body = await _deep(guest_client)
    assert body["http"] == 503
    assert body["status"] == "down"
    assert body["checks"]["storage"]["status"] == "down"


async def test_unconfigured_modal_backend_is_down(app: Any, guest_client: AsyncClient) -> None:
    _override_settings(app, generation_backend="modal", modal_endpoint_url="")
    body = await _deep(guest_client)
    assert body["http"] == 503
    assert body["checks"]["video_backend"]["status"] == "down"


async def test_modal_reachability_never_invokes_adapters(
    app: Any, guest_client: AsyncClient, monkeypatch: Any
) -> None:
    real_open = asyncio.open_connection

    async def _fake_open(host: str, *args: Any, **kwargs: Any) -> Any:
        if host == "modal.example":
            return None, _FakeWriter()
        return await real_open(host, *args, **kwargs)

    async def _must_not_run(self: Any, request: Any) -> Any:
        raise AssertionError("adapter invoked by a health check")

    monkeypatch.setattr(asyncio, "open_connection", _fake_open)
    monkeypatch.setattr(ModalAdapter, "generate_video", _must_not_run)
    monkeypatch.setattr(ModalImageAdapter, "generate_image", _must_not_run)
    _override_settings(app, generation_backend="modal",
                       modal_endpoint_url="https://modal.example/clip",
                       image_generation_backend="modal",
                       modal_image_endpoint_url="https://modal.example/images")
    body = await _deep(guest_client)
    assert body["checks"]["video_backend"]["status"] == "ok"
    assert body["checks"]["image_backend"]["status"] == "ok"


async def test_queue_depth_reflects_queued_job(app: Any, guest_client: AsyncClient,
                                               object_storage: InMemoryObjectStorage) -> None:
    _override_settings(app, generation_backend="local-motion")
    await create_queued_job(guest_client, object_storage, "deep-queue-1")
    body = await _deep(guest_client)
    assert body["checks"]["queue"]["detail"]["depth"] >= 1
    assert body["checks"]["queue"]["detail"]["oldest_age_seconds"] is not None


async def test_shallow_health_unchanged(guest_client: AsyncClient) -> None:
    response = await guest_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
