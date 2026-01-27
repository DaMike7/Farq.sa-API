# app/tasks/csv_import.py

import os
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.core.database import AsyncSessionLocal
from app.models.restaurant import Restaurant
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def import_csv_to_db(self, file_path: str):
    logger.info(f"Task started: importing CSV from {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    try:
        df = pd.read_csv(file_path)
        logger.info(f"CSV loaded with {len(df)} rows")

        required = ["name", "latitude", "longitude"]
        if not all(col in df.columns for col in required):
            raise ValueError(f"Missing required columns: {required}")

        df = df[required + [c for c in df.columns if c not in required]]
        df = df.dropna(subset=["latitude", "longitude"])
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        df = df.dropna(subset=["latitude", "longitude"])

        records = df.to_dict(orient="records")
        logger.info(f"Processed {len(records)} valid records")

        async def run_import():
            async with AsyncSessionLocal() as db:
                stmt = insert(Restaurant).values([
                    {
                        "name": r["name"],
                        "latitude": float(r["latitude"]),
                        "longitude": float(r["longitude"]),
                        "address": r.get("address"),
                        "city": r.get("city"),
                        "category": r.get("category"),
                        "source": r.get("source"),
                        "geom": f"SRID=4326;POINT({r['longitude']} {r['latitude']})"
                    }
                    for r in records
                ]).on_conflict_do_nothing()

                await db.execute(stmt)
                await db.commit()
                logger.info("DB insert completed")

        import asyncio
        asyncio.run(run_import())

        logger.info(f"Successfully imported {len(records)} restaurants")
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")

    except Exception as exc:
        logger.error(f"Import failed for {file_path}: {exc}", exc_info=True)
        if os.path.exists(file_path):
            os.remove(file_path)
        raise self.retry(exc=exc)