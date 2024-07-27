import argparse
import asyncio
import json
import logging
import os

import sqlalchemy.exc
from dotenv import load_dotenv
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker
from datetime import datetime, date

from fastapi_app.postgres_engine import (
    create_postgres_engine_from_args,
    create_postgres_engine_from_env,
)
from fastapi_app.postgres_models import Item, Kefi_Event

logger = logging.getLogger("ragapp")


def string_to_date(date_string):
    if not date_string or date_string.lower() in ['none', 'null', '']:
        date_string = "2025-04-04"
    
    date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    
    # If none of the formats match, raise an error or return None
    raise ValueError(f"Unable to parse date string: {date_string}")


async def seed_data_items(engine):
    # Check if Item table exists
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'items')"  # noqa
            )
        )
        if not result.scalar():
            logger.error("Items table does not exist. Please run the database setup script first.")
            return

    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        # Insert the items from the JSON file into the database
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "seed_data.json")) as f:
            catalog_items = json.load(f)
            for catalog_item in catalog_items:
                item = await session.execute(select(Item).filter(Item.id == catalog_item["Id"]))
                if item.scalars().first():
                    continue
                item = Item(
                    id=catalog_item["Id"],
                    type=catalog_item["Type"],
                    brand=catalog_item["Brand"],
                    name=catalog_item["Name"],
                    description=catalog_item["Description"],
                    price=catalog_item["Price"],
                    embedding=catalog_item["Embedding"],
                )
                session.add(item)
            try:
                await session.commit()
            except sqlalchemy.exc.IntegrityError:
                pass

    logger.info("Items table seeded successfully.")


async def seed_data_events(engine):
    # Check if kefi_events table exists
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'kefi_events')"  # noqa
            )
        )
        if not result.scalar():
            logger.error("kefi_events table does not exist. Please run the database setup script first.")
            return

    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        # Insert the events from the JSON file into the database
        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, "seed_data_events.json"), encoding="utf-8") as f:
            miami_events = json.load(f)

            for miami_event in miami_events:
                kefi_event = await session.execute(select(Kefi_Event).filter(Kefi_Event.id == miami_event["Id"]))
                if kefi_event.scalars().first():
                    continue
                kefi_event = Kefi_Event(
                    id=miami_event["Id"],
                    name=miami_event["Name"],
                    description=miami_event["Description"],
                    category=miami_event["Category"],
                    price=miami_event["Price"],
                    start_date=miami_event["Start Date"],
                    start_date_typed=string_to_date(miami_event["Start Date"]),
                    embedding=miami_event["Embedding"],
                )
                session.add(kefi_event)
            try:
                await session.commit()
            except sqlalchemy.exc.IntegrityError:
                pass

    logger.info("Kefi_Events table seeded successfully.")


async def main():
    parser = argparse.ArgumentParser(description="Create database schema")
    parser.add_argument("--host", type=str, help="Postgres host")
    parser.add_argument("--username", type=str, help="Postgres username")
    parser.add_argument("--password", type=str, help="Postgres password")
    parser.add_argument("--database", type=str, help="Postgres database")
    parser.add_argument("--sslmode", type=str, help="Postgres sslmode")

    # if no args are specified, use environment variables
    args = parser.parse_args()
    if args.host is None:
        engine = await create_postgres_engine_from_env()
    else:
        engine = await create_postgres_engine_from_args(args)

    await seed_data_items(engine)
    await seed_data_events(engine)

    await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    logger.setLevel(logging.INFO)
    load_dotenv(override=True)
    asyncio.run(main())
