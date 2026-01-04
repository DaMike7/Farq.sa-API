# app/services/geo_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from geoalchemy2.functions import ST_DWithin, ST_DistanceSphere, ST_MakePoint
from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantResponse
from typing import List

class GeoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 5000,
        limit: int = 20
    ) -> List[RestaurantResponse]:
        point = ST_MakePoint(longitude, latitude).ST_Buffer(0)

        stmt = (
            select(Restaurant)
            .filter(ST_DWithin(Restaurant.geom, point, radius_meters))
            .order_by(ST_DistanceSphere(Restaurant.geom, point))
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        restaurants = result.scalars().all()

        responses = []
        for r in restaurants:
            distance = await self._get_distance_meters(r.geom, point)
            data = r.__dict__
            data["distance_meters"] = round(distance) if distance is not None else None
            responses.append(RestaurantResponse(**data))

        return responses

    async def _get_distance_meters(self, geom1, geom2):
        result = await self.db.execute(select(ST_DistanceSphere(geom1, geom2)))
        return result.scalar_one_or_none()