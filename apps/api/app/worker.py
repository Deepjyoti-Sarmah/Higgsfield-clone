import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import create_database_engine
from app.settings import get_settings

HEARTBEAT_SECONDS = 10
logger = logging.getLogger("worker")


async def run_heartbeat_loop() -> None:
    engine = create_database_engine(get_settings())
    try:
        while True:
            try:
                async with engine.connect() as connection:
                    await connection.execute(text("select 1"))
                logger.info("worker heartbeat: database ok")
            except (SQLAlchemyError, OSError) as error:
                logger.error("worker heartbeat: database down (%s)", error)
            await asyncio.sleep(HEARTBEAT_SECONDS)
    finally:
        await engine.dispose()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    asyncio.run(run_heartbeat_loop())


if __name__ == "__main__":
    main()
