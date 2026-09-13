import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage
from app.db import get_session
from app.services import share_html, share_views
from app.settings import Settings, get_settings
from app.storage_dependencies import get_object_storage

router = APIRouter(tags=["share-page"])


def parse_job_id(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


@router.get("/v/{job_id}", response_class=HTMLResponse, include_in_schema=False)
async def read_share_page(
    job_id: str,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> HTMLResponse:
    # A malformed or unknown id is still a rendered page: the client shows the not-found state.
    parsed_id = parse_job_id(job_id)
    view = None if parsed_id is None else await share_views.read_public_job(
        session, storage, settings, parsed_id
    )
    document = share_html.render_share_page(
        shell=share_html.read_shell(settings.static_dir),
        view=view,
        share_url=share_html.share_url_for(str(request.base_url), job_id),
    )
    return HTMLResponse(document)
