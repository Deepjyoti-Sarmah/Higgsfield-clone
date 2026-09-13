from typing import Literal

from pydantic import BaseModel, ConfigDict

PresetCategory = Literal["camera", "cinematic", "dynamic"]


class PresetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    description: str
    category: PresetCategory
    credit_cost: int
    preview_url: str | None


class PresetListResponse(BaseModel):
    presets: list[PresetResponse]
