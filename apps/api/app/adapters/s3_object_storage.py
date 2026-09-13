import asyncio
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.settings import Settings

MISSING_OBJECT_CODES = {"404", "NoSuchKey", "NotFound"}


class S3ObjectStorage:
    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.s3_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def create_upload_url(self, key: str, content_type: str, expires_seconds: int) -> str:
        url = self._client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self._bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_seconds,
        )
        return str(url)

    def create_download_url(self, key: str, expires_seconds: int) -> str:
        url = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )
        return str(url)

    async def read_object_size(self, key: str) -> int | None:
        try:
            head = await asyncio.to_thread(self._client.head_object, Bucket=self._bucket, Key=key)
        except ClientError as error:
            if error.response["Error"]["Code"] in MISSING_OBJECT_CODES:
                return None
            raise
        return int(head["ContentLength"])

    async def download_to_path(self, key: str, path: Path) -> None:
        await asyncio.to_thread(self._client.download_file, self._bucket, key, str(path))

    async def upload_from_path(self, key: str, path: Path, content_type: str) -> None:
        await asyncio.to_thread(
            self._client.upload_file,
            str(path),
            self._bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

    async def delete_object(self, key: str) -> None:
        await asyncio.to_thread(self._client.delete_object, Bucket=self._bucket, Key=key)
