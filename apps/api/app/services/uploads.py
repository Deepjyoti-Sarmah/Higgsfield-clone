import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.object_storage import ObjectStorage, build_asset_url
from app.models.asset import Asset
from app.repositories.assets import find_user_asset, insert_asset, mark_asset_ready
from app.settings import Settings

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
EXTENSIONS_BY_CONTENT_TYPE = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class UploadNotFoundError(Exception):
    """The asset does not exist or belongs to another user."""


class UploadObjectMissingError(Exception):
    """The browser has not finished the presigned PUT yet."""


class UploadSizeMismatchError(Exception):
    """The stored object is larger than the limit or differs from the declared size."""


@dataclass(frozen=True)
class PendingUpload:
    asset: Asset
    upload_url: str
    expires_at: datetime


@dataclass(frozen=True)
class CompletedUpload:
    asset: Asset
    url: str


def build_input_storage_key(
    user_id: uuid.UUID, asset_id: uuid.UUID, content_type: str
) -> str:
    return f"users/{user_id}/inputs/{asset_id}.{EXTENSIONS_BY_CONTENT_TYPE[content_type]}"


async def create_pending_upload(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    *,
    user_id: uuid.UUID,
    content_type: str,
    byte_size: int,
) -> PendingUpload:
    asset_id = uuid.uuid4()
    key = build_input_storage_key(user_id, asset_id, content_type)
    asset = await insert_asset(
        session,
        asset_id=asset_id,
        user_id=user_id,
        kind="input_image",
        status="pending",
        storage_key=key,
        content_type=content_type,
        byte_size=byte_size,
    )
    await session.commit()
    upload_url = storage.create_upload_url(key, content_type, settings.upload_url_ttl_seconds)
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.upload_url_ttl_seconds)
    return PendingUpload(asset=asset, upload_url=upload_url, expires_at=expires_at)


async def mark_upload_complete(
    session: AsyncSession,
    storage: ObjectStorage,
    settings: Settings,
    *,
    user_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> CompletedUpload:
    asset = await find_user_asset(session, user_id, asset_id)
    if asset is None:
        raise UploadNotFoundError(str(asset_id))
    if asset.status == "ready":
        return CompletedUpload(asset=asset, url=_asset_url(storage, settings, asset))
    stored_size = await storage.read_object_size(asset.storage_key)
    if stored_size is None:
        raise UploadObjectMissingError(asset.storage_key)
    if stored_size > MAX_UPLOAD_BYTES or stored_size != asset.byte_size:
        await storage.delete_object(asset.storage_key)
        raise UploadSizeMismatchError(f"stored={stored_size} declared={asset.byte_size}")
    await mark_asset_ready(session, asset, stored_size)
    await session.commit()
    return CompletedUpload(asset=asset, url=_asset_url(storage, settings, asset))


def _asset_url(storage: ObjectStorage, settings: Settings, asset: Asset) -> str:
    return build_asset_url(
        storage, asset.storage_key, settings.s3_public_base_url, settings.download_url_ttl_seconds
    )
