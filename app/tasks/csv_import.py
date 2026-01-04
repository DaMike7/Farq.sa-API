import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from geoalchemy2 import Geography
from app.models.restaurant import Restaurant
from app.core.database import AsyncSessionLocal

async def import_csv_to_db(file_path: str):
    async with AsyncSessionLocal() as db:
        df = pd.read_csv(file_path)
        
        required_columns = ["name", "latitude", "longitude"]
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"CSV must contain columns: {required_columns}")
        
        df = df[required_columns + [c for c in ["address", "city", "category", "source"] if c in df.columns]]
        df = df.dropna(subset=["latitude", "longitude"])
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        df = df.dropna(subset=["latitude", "longitude"])
        
        records = df.to_dict(orient="records")
        
        stmt = insert(Restaurant).values([
            {
                "name": r["name"],
                "latitude": r["latitude"],
                "longitude": r["longitude"],
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