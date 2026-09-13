from pathlib import Path


class InMemoryObjectStorage:
    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {}

    def create_upload_url(self, key: str, content_type: str, expires_seconds: int) -> str:
        return f"memory://{key}"

    def create_download_url(self, key: str, expires_seconds: int) -> str:
        return f"memory://{key}?get"

    async def read_object_size(self, key: str) -> int | None:
        content = self._objects.get(key)
        return None if content is None else len(content)

    async def download_to_path(self, key: str, path: Path) -> None:
        path.write_bytes(self._objects[key])

    async def upload_from_path(self, key: str, path: Path, content_type: str) -> None:
        self._objects[key] = path.read_bytes()

    async def delete_object(self, key: str) -> None:
        self._objects.pop(key, None)

    def put_bytes(self, key: str, content: bytes) -> None:
        self._objects[key] = content
