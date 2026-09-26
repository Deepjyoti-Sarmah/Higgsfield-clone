"""One-off: set duration_ms on succeeded video jobs created before the T-050 fix.

From apps/api, with the api service env:
  railway run -s api .venv/bin/python scripts/backfill_clip_durations.py [--dry-run]
"""
import asyncio
import subprocess
import sys
import tempfile
from pathlib import Path

from sqlalchemy import select

from app.adapters.s3_object_storage import S3ObjectStorage
from app.db import create_database_engine, create_session_maker
from app.models import asset, preset, user  # noqa: F401 (FK registration)
from app.models.asset import Asset
from app.models.job import Job
from app.settings import get_settings


def probe_duration_ms(path: Path) -> int | None:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=False)
    try:
        return int(float(result.stdout.strip()) * 1000)
    except ValueError:
        return None


async def main(dry_run: bool, limit: int | None) -> None:
    settings = get_settings()
    storage = S3ObjectStorage(settings)
    engine = create_database_engine(settings)
    maker = create_session_maker(engine)
    updated, skipped = 0, 0
    async with maker() as session:
        statement = select(Job).where(
            Job.kind == "video", Job.status == "succeeded", Job.duration_ms.is_(None),
            Job.output_video_asset_id.is_not(None))
        jobs = (await session.execute(statement)).scalars().all()
        if limit is not None:
            jobs = jobs[:limit]
        print(f"candidates={len(jobs)} dry_run={dry_run}", flush=True)
        for job in jobs:
            target = await session.get(Asset, job.output_video_asset_id)
            if target is None:
                skipped += 1
                continue
            try:
                with tempfile.TemporaryDirectory(prefix="bf-dur-") as directory:
                    path = Path(directory) / "video.mp4"
                    await storage.download_to_path(target.storage_key, path)
                    duration = probe_duration_ms(path)
            except Exception as error:  # orphan assets: the object is gone
                print(f"job {job.id} skipped: {error}", flush=True)
                skipped += 1
                continue
            if duration:
                job.duration_ms = duration
                updated += 1
                if not dry_run:
                    await session.commit()
                print(f"job {job.id} -> {duration}ms", flush=True)
            else:
                skipped += 1
        if dry_run:
            await session.rollback()
        else:
            await session.commit()
    await engine.dispose()
    print(f"updated={updated} skipped={skipped}", flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    main_args = {"dry_run": "--dry-run" in args, "limit": None}
    if "--limit" in args:
        main_args["limit"] = int(args[args.index("--limit") + 1])
    asyncio.run(main(**main_args))
