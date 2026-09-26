import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fit_input import fit_to_output  # noqa: E402


def _solid(width: int, height: int) -> Image.Image:
    return Image.new("RGB", (width, height), color=(10, 20, 30))


def test_wide_image_fits_landscape() -> None:
    image, width, height = fit_to_output(_solid(2000, 1000))
    assert (width, height) == (960, 544)
    assert image.size == (960, 544)


def test_tall_image_fits_portrait() -> None:
    image, width, height = fit_to_output(_solid(1000, 2000))
    assert (width, height) == (544, 960)
    assert image.size == (544, 960)


def test_near_square_image_fits_square() -> None:
    image, width, height = fit_to_output(_solid(1000, 1050))
    assert (width, height) == (704, 704)
    assert image.size == (704, 704)


def test_tiny_image_still_resizes_up() -> None:
    image, width, height = fit_to_output(_solid(40, 20))
    assert (width, height) == (960, 544)
    assert image.size == (960, 544)


def test_output_dimensions_are_multiples_of_32() -> None:
    for size in [(2000, 1000), (1000, 2000), (1000, 1050)]:
        _, width, height = fit_to_output(_solid(*size))
        assert width % 32 == 0
        assert height % 32 == 0
