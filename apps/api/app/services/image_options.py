from app.domain.image_rules import (
    ASPECT_RATIOS,
    IMAGE_CREDIT_COST_HIGH,
    IMAGE_CREDIT_COST_STANDARD,
    MAX_IMAGE_COUNT,
    QUALITIES,
)
from app.schemas.image_jobs import ImageCreditCosts, ImageOptionsResponse


def read_image_options() -> ImageOptionsResponse:
    return ImageOptionsResponse(
        aspect_ratios=list(ASPECT_RATIOS),
        qualities=list(QUALITIES),
        max_count=MAX_IMAGE_COUNT,
        credit_costs=ImageCreditCosts(
            standard=IMAGE_CREDIT_COST_STANDARD, high=IMAGE_CREDIT_COST_HIGH
        ),
    )
