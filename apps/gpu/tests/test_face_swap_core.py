"""Unit tests for the pure parts of face_swap_core: picking, boxes, blending."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from face_swap_core import (  # noqa: E402
    NO_FACE_IN_SOURCE,
    NoFaceError,
    clamp_box,
    face_area,
    feather_mask,
    paste_with_mask,
    pick_largest_face,
    require_source_face,
    require_target_faces,
    square_box,
)


class FakeFace:
    def __init__(self, bbox):
        self.bbox = bbox


def test_face_area_computes_width_times_height():
    assert face_area((0, 0, 10, 5)) == 50


def test_pick_largest_face_returns_biggest_box():
    small = FakeFace((0, 0, 10, 10))
    big = FakeFace((0, 0, 50, 50))
    assert pick_largest_face([small, big]) is big


def test_pick_largest_face_empty_list_returns_none():
    assert pick_largest_face([]) is None


def test_require_source_face_raises_with_user_safe_message():
    with pytest.raises(NoFaceError, match=NO_FACE_IN_SOURCE):
        require_source_face([])


def test_require_target_faces_raises_on_empty():
    with pytest.raises(NoFaceError):
        require_target_faces([])


def test_require_target_faces_returns_list_unchanged():
    faces = [FakeFace((0, 0, 1, 1))]
    assert require_target_faces(faces) is faces


def test_clamp_box_stays_within_image_bounds():
    assert clamp_box((-5, -5, 1000, 1000), 100, 80) == (0, 0, 100, 80)


def test_clamp_box_keeps_normal_box_unchanged():
    assert clamp_box((10, 20, 30, 40), 100, 100) == (10, 20, 30, 40)


def test_feather_mask_is_one_at_center_and_fades_at_edge():
    mask = feather_mask(40, 40, feather_px=6)
    assert mask[20, 20] == pytest.approx(1.0)
    assert mask[0, 0] < 1.0


def test_paste_with_mask_full_mask_replaces_region():
    base = np.zeros((10, 10, 3), dtype=np.uint8)
    patch = np.full((4, 4, 3), 255, dtype=np.uint8)
    mask = np.ones((4, 4), dtype=np.float32)
    result = paste_with_mask(base, patch, mask, (2, 2))
    assert (result[2:6, 2:6] == 255).all()
    assert (result[0, 0] == 0).all()


def test_square_box_makes_a_square_from_a_wide_rectangle():
    x1, y1, x2, y2 = square_box((400, 400, 480, 420), image_width=1000, image_height=1000)
    assert (x2 - x1) == pytest.approx(y2 - y1, abs=1)


def test_square_box_stays_within_image_bounds():
    x1, y1, x2, y2 = square_box((0, 0, 900, 950), image_width=1000, image_height=1000)
    assert 0 <= x1 and x2 <= 1000
    assert 0 <= y1 and y2 <= 1000


def test_paste_with_mask_zero_mask_keeps_base():
    base = np.full((10, 10, 3), 7, dtype=np.uint8)
    patch = np.full((4, 4, 3), 255, dtype=np.uint8)
    mask = np.zeros((4, 4), dtype=np.float32)
    result = paste_with_mask(base, patch, mask, (2, 2))
    assert (result == 7).all()
