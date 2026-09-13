from httpx import AsyncClient

from app.domain.credit_rules import VIDEO_CREDIT_COST

PRESET_FIELDS = {"slug", "name", "description", "category", "credit_cost", "preview_url"}
CATEGORIES = {"camera", "cinematic", "dynamic"}


async def test_presets_are_listed_signed_out(client: AsyncClient) -> None:
    response = await client.get("/api/v1/presets")

    assert response.status_code == 200
    presets = response.json()["presets"]
    assert len(presets) >= 12


async def test_every_preset_has_the_contract_fields(client: AsyncClient) -> None:
    presets = (await client.get("/api/v1/presets")).json()["presets"]

    for preset in presets:
        assert set(preset) == PRESET_FIELDS
        assert preset["category"] in CATEGORIES
        assert preset["name"]
        assert preset["description"]
        assert preset["preview_url"] is None or isinstance(preset["preview_url"], str)


async def test_presets_cost_one_video_price_and_are_sorted(client: AsyncClient) -> None:
    presets = (await client.get("/api/v1/presets")).json()["presets"]

    assert [preset["credit_cost"] for preset in presets] == [VIDEO_CREDIT_COST] * len(presets)
    assert len({preset["slug"] for preset in presets}) == len(presets)
