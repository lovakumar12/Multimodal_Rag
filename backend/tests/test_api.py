import pytest
import httpx
from backend.app.main import app


@pytest.mark.anyio
async def test_health_and_ready_endpoints():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        # 2. Ready
        res_ready = await client.get("/ready")
        assert res_ready.status_code == 200
        assert "database" in res_ready.json()

        # 3. Stats
        res_stats = await client.get("/stats")
        assert res_stats.status_code == 200
        assert "total_documents" in res_stats.json()


@pytest.mark.anyio
async def test_knowledge_base_crud():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Create KB
        res = await client.post(
            "/api/v1/knowledge-bases",
            json={"name": "Engineering Docs", "description": "System architecture specs"},
        )
        assert res.status_code == 201
        data = res.json()
        kb_id = data["id"]
        assert data["name"] == "Engineering Docs"

        # Get KB
        res_get = await client.get(f"/api/v1/knowledge-bases/{kb_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == kb_id

        # List KBs
        res_list = await client.get("/api/v1/knowledge-bases")
        assert res_list.status_code == 200
        ids = [kb["id"] for kb in res_list.json()]
        assert kb_id in ids

        # Delete KB
        res_del = await client.delete(f"/api/v1/knowledge-bases/{kb_id}")
        assert res_del.status_code == 204
