import json

from fastapi import APIRouter, Query

from app.database import get_db

router = APIRouter(prefix="/api")


@router.get("/logs")
async def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    level: str | None = None,
    source: str | None = None,
):
    base_conditions = []
    params: list = []

    if level:
        base_conditions.append("level = ?")
        params.append(level)
    if source:
        base_conditions.append("source LIKE ?")
        params.append(f"%{source}%")

    where_clause = (" WHERE " + " AND ".join(base_conditions)) if base_conditions else ""

    # Total count for pagination
    count_query = f"SELECT COUNT(*) FROM logs{where_clause}"
    # Data query with LIMIT/OFFSET at DB level
    data_query = f"SELECT id, timestamp, level, source, message, details FROM logs{where_clause} ORDER BY id DESC LIMIT ? OFFSET ?"
    data_params = params + [limit, offset]

    async with get_db() as db:
        cursor = await db.execute(count_query, params)
        total = (await cursor.fetchone())[0]

        cursor = await db.execute(data_query, data_params)
        rows = await cursor.fetchall()

    return {
        "items": [
            {
                "id": row[0],
                "timestamp": row[1],
                "level": row[2],
                "source": row[3],
                "message": row[4],
                "details": json.loads(row[5]) if row[5] else None,
            }
            for row in rows
        ],
        "total": total,
    }
