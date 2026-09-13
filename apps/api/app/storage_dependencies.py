from functools import lru_cache

from app.adapters.object_storage import ObjectStorage
from app.adapters.s3_object_storage import S3ObjectStorage
from app.settings import get_settings


@lru_cache
def get_object_storage() -> ObjectStorage:
    return S3ObjectStorage(get_settings())
