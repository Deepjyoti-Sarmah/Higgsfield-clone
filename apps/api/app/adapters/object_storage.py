from pathlib import Path
from typing import Protocol


class ObjectStorage(Protocol):
    def create_upload_url(self, key: str, content_type: str, expires_seconds: int) -> str: ...

    def create_download_url(self, key: str, expires_seconds: int) -> str: ...

    async def read_object_size(self, key: str) -> int | None: ...

    async def download_to_path(self, key: str, path: Path) -> None: ...

    async def upload_from_path(self, key: str, path: Path, content_type: str) -> None: ...

    async def delete_object(self, key: str) -> None: ...


def build_asset_url(
    storage: ObjectStorage, key: str, public_base_url: str, expires_seconds: int
) -> str:
    if public_base_url:
        return f"{public_base_url.rstrip('/')}/{key}"
    return storage.create_download_url(key, expires_seconds)
