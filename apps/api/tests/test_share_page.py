import uuid
from html import escape
from pathlib import Path

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.share_html import FAILED_DESCRIPTION, GENERATING_DESCRIPTION, UNKNOWN_DESCRIPTION
from app.settings import Settings, get_settings
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import PRESET_NAME, create_queued_job, current_user_id

PRIVATE_FAILURE_TEXT = "private provider failure text"
HOSTILE_PRESET_NAME = 'Bad "Name" <script>alert(1)</script>'
OUTPUT_ASSETS = (
    ("output_video", "video.mp4", "video/mp4"),
    ("output_poster", "poster.jpg", "image/jpeg"),
)
SessionMaker = async_sessionmaker[AsyncSession]


async def _run_sql(session_maker: SessionMaker, statement: str, params: dict[str, object]) -> None:
    async with session_maker() as session:
        await session.execute(text(statement), params)
        await session.commit()


async def _insert_ready_asset(
    session_maker: SessionMaker,
    user_id: str,
    asset_id: uuid.UUID,
    kind: str,
    storage_key: str,
    content_type: str,
) -> None:
    await _run_sql(
        session_maker,
        "INSERT INTO asset (id, user_id, kind, status, storage_key, content_type, byte_size)"
        " VALUES (:id, :user_id, :kind, 'ready', :storage_key, :content_type, 99)",
        {
            "id": asset_id,
            "user_id": uuid.UUID(user_id),
            "kind": kind,
            "storage_key": storage_key,
            "content_type": content_type,
        },
    )


async def _update_job(session_maker: SessionMaker, job_id: uuid.UUID, **columns: object) -> None:
    assignments = ", ".join(f"{name} = :{name}" for name in columns)
    await _run_sql(
        session_maker,
        f"UPDATE job SET {assignments} WHERE id = :job_id",
        {**columns, "job_id": job_id},
    )


async def _make_succeeded_job(
    session_maker: SessionMaker,
    guest_client: AsyncClient,
    storage: InMemoryObjectStorage,
    key: str,
) -> str:
    job_id = uuid.UUID(await create_queued_job(guest_client, storage, key))
    user_id = await current_user_id(guest_client)
    asset_ids: dict[str, uuid.UUID] = {}
    for kind, filename, content_type in OUTPUT_ASSETS:
        asset_id = uuid.uuid4()
        asset_ids[kind] = asset_id
        await _insert_ready_asset(
            session_maker, user_id, asset_id, kind, f"users/{user_id}/jobs/{job_id}/{filename}",
            content_type,
        )
    await _update_job(
        session_maker,
        job_id,
        status="succeeded",
        output_video_asset_id=asset_ids["output_video"],
        output_poster_asset_id=asset_ids["output_poster"],
    )
    return str(job_id)


async def test_no_cookie_gets_html_with_the_job_meta_tags(
    client: AsyncClient, guest_client: AsyncClient, object_storage: InMemoryObjectStorage
) -> None:
    job_id = await create_queued_job(guest_client, object_storage, "share-page-queued-1")

    response = await client.get(f"/v/{job_id}")
    body = response.text

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert f"<title>{PRESET_NAME} \u00b7 Higgsfield</title>" in body
    for tag in ("og:title", "og:description", "og:type", "og:url", "twitter:card", "twitter:title"):
        assert tag in body
    assert 'name="twitter:card" content="summary_large_image"' in body
    assert GENERATING_DESCRIPTION in body
    assert "og:video" not in body
    assert "<video" not in body


async def test_succeeded_job_adds_the_video_and_image_tags(
    client: AsyncClient,
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: SessionMaker,
) -> None:
    job_id = await _make_succeeded_job(session_maker, guest_client, object_storage, "share-page-done-1")

    response = await client.get(f"/v/{job_id}")
    body = response.text

    assert response.status_code == 200
    assert "og:video" in body
    assert "og:image" in body
    assert 'name="twitter:image"' in body
    assert 'name="twitter:card" content="player"' in body
    assert "video.mp4?get" in body
    assert "poster.jpg?get" in body


async def test_unknown_or_malformed_id_returns_generic_html(client: AsyncClient) -> None:
    for path in (f"/v/{uuid.uuid4()}", "/v/not-a-uuid"):
        response = await client.get(path)

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "og:title" in response.text
        assert UNKNOWN_DESCRIPTION in response.text


async def test_failed_job_hides_the_private_error_text(
    client: AsyncClient,
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: SessionMaker,
) -> None:
    job_id = await create_queued_job(guest_client, object_storage, "share-page-fail-1")
    await _update_job(
        session_maker, uuid.UUID(job_id), status="failed", error_message=PRIVATE_FAILURE_TEXT
    )

    response = await client.get(f"/v/{job_id}")

    assert response.status_code == 200
    assert escape(FAILED_DESCRIPTION, quote=True) in response.text
    assert PRIVATE_FAILURE_TEXT not in response.text
    assert "og:video" not in response.text
    assert "<video" not in response.text


async def test_preset_name_is_escaped_inside_content_attributes(
    client: AsyncClient,
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: SessionMaker,
) -> None:
    rename = "UPDATE preset SET name = :name WHERE slug = :slug"
    await _run_sql(session_maker, rename, {"name": HOSTILE_PRESET_NAME, "slug": "dolly-in"})
    try:
        job_id = await create_queued_job(guest_client, object_storage, "share-page-escape-1")
        body = (await client.get(f"/v/{job_id}")).text
    finally:
        await _run_sql(session_maker, rename, {"name": PRESET_NAME, "slug": "dolly-in"})

    assert HOSTILE_PRESET_NAME not in body
    assert "&lt;script&gt;" in body
    assert "&quot;Name&quot;" in body
    assert 'content="Bad "Name"' not in body


async def test_missing_index_falls_back_to_the_builtin_shell(
    app: FastAPI, client: AsyncClient, tmp_path: Path
) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(static_dir=str(tmp_path))
    try:
        response = await client.get(f"/v/{uuid.uuid4()}")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "og:title" in response.text
    assert UNKNOWN_DESCRIPTION in response.text
    assert response.text.count("</head>") == 1
