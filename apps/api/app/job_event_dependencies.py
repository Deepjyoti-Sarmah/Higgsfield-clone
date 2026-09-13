from fastapi import Request

from app.services.job_event_broker import JobEventBroker


async def get_job_event_broker(request: Request) -> JobEventBroker:
    broker: JobEventBroker = request.app.state.job_event_broker
    return broker
