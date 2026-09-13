import asyncio
import uuid

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.job_event_broker import parse_job_id
from app.services.job_event_stream import stream_job_status_events
from tests.fakes.in_memory_object_storage import InMemoryObjectStorage
from tests.job_api_helpers import create_queued_job
from tests.job_event_helpers import (
    collect_events,
    drive_to_completion,
    notify_only,
    open_broker,
    status_of,
    transition,
    wait_for_wake_up,
)


async def test_stream_sends_queued_running_succeeded_within_a_second_each(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "events-seq-key1"))
    async with open_broker(session_maker) as broker:
        collected = await asyncio.gather(
            collect_events(job_id, broker, session_maker),
            drive_to_completion(session_maker, job_id),
        )
    frames, seen_at = collected[0]

    assert [status_of(frame) for frame in frames] == ["queued", "running", "succeeded"]
    assert seen_at[0] < 1.0
    assert seen_at[1] - seen_at[0] < 1.0
    assert seen_at[2] - seen_at[1] < 1.0


async def test_stream_pings_while_the_status_does_not_change(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "events-ping-key1"))
    async with open_broker(session_maker) as broker:
        stream = stream_job_status_events(job_id, broker, session_maker, ping_seconds=0.15)
        preamble = await stream.__anext__()
        first = await stream.__anext__()
        ping = await stream.__anext__()
        await stream.aclose()

    assert preamble == "retry: 3000\n\n"
    assert status_of(first) == "queued"
    assert ping == ": ping\n\n"


async def test_stream_closes_immediately_for_a_terminal_job(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "events-done-key1"))
    await transition(session_maker, job_id, "failed")
    async with open_broker(session_maker) as broker:
        chunks = [chunk async for chunk in stream_job_status_events(job_id, broker, session_maker)]

    assert chunks == [
        "retry: 3000\n\n",
        f'event: status\ndata: {{"job_id":"{job_id}","status":"failed"}}\n\n',
    ]


async def test_broker_wakes_a_subscriber_on_a_real_notification(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "events-notify-1"))
    async with open_broker(session_maker) as broker:
        queue = broker.subscribe(job_id)
        await notify_only(session_maker, job_id)
        woke = await wait_for_wake_up(queue)

    assert woke


async def test_broker_wakes_every_subscriber_after_a_listener_reconnect(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "events-reconnect"))
    async with open_broker(session_maker) as broker:
        queue = broker.subscribe(job_id)
        broker._listener.terminate()
        woke = await wait_for_wake_up(queue, seconds=5.0)

    assert woke


async def test_unsubscribe_stops_the_wake_ups(
    guest_client: AsyncClient,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "events-drop-key1"))
    async with open_broker(session_maker) as broker:
        queue = broker.subscribe(job_id)
        broker.unsubscribe(job_id, queue)
        await notify_only(session_maker, job_id)
        woke = await wait_for_wake_up(queue)

    assert not woke


async def test_stream_for_an_unknown_job_ends_after_the_preamble(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    async with open_broker(session_maker) as broker:
        chunks = [
            chunk async for chunk in stream_job_status_events(uuid.uuid4(), broker, session_maker)
        ]

    assert chunks == ["retry: 3000\n\n"]


async def test_events_endpoint_streams_for_the_owner(
    guest_client: AsyncClient,
    app: FastAPI,
    object_storage: InMemoryObjectStorage,
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    job_id = uuid.UUID(await create_queued_job(guest_client, object_storage, "events-owner-key"))
    await transition(session_maker, job_id, "failed")
    async with open_broker(session_maker) as broker:
        app.state.job_event_broker = broker
        try:
            response = await guest_client.get(f"/api/v1/jobs/{job_id}/events")
        finally:
            del app.state.job_event_broker

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"
    assert f'data: {{"job_id":"{job_id}","status":"failed"}}' in response.text


async def test_events_endpoint_without_a_cookie_is_401(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/jobs/{uuid.uuid4()}/events")

    assert response.status_code == 401


def test_job_routes_keep_their_published_status_codes(app: FastAPI) -> None:
    post_responses = app.openapi()["paths"]["/api/v1/jobs"]["post"]["responses"]

    assert {"202", "402", "404", "409"} <= set(post_responses)


def test_notify_payload_parsing_ignores_junk() -> None:
    job_id = uuid.uuid4()

    assert parse_job_id(f'{{"job_id":"{job_id}"}}') == job_id
    assert parse_job_id("not json") is None
    assert parse_job_id('{"job_id":"nope"}') is None
