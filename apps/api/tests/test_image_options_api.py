from httpx import AsyncClient

from app.domain.image_rules import (
    ASPECT_RATIOS,
    IMAGE_CREDIT_COST_HIGH,
    IMAGE_CREDIT_COST_STANDARD,
    MAX_IMAGE_COUNT,
    QUALITIES,
)


async def test_image_options_are_public_and_complete(client: AsyncClient) -> None:
    response = await client.get("/api/v1/image-options")

    assert response.status_code == 200
    body = response.json()
    assert body["aspect_ratios"] == list(ASPECT_RATIOS)
    assert body["qualities"] == list(QUALITIES)
    assert body["max_count"] == MAX_IMAGE_COUNT
    assert body["credit_costs"] == {
        "standard": IMAGE_CREDIT_COST_STANDARD,
        "high": IMAGE_CREDIT_COST_HIGH,
    }
