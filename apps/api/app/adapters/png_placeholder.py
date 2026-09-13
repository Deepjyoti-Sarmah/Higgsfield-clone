import struct
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
TRUE_COLOR = 2
BIT_DEPTH = 8
FILTER_NONE = 0


def _chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def _pixel(x: int, y: int, width: int, height: int, seed: int) -> tuple[int, int, int]:
    red = (x * 255) // max(width - 1, 1)
    green = (y * 255) // max(height - 1, 1)
    blue = (seed * 37 + x * 3 + y * 5) % 256
    return red, green, blue


def write_placeholder_png(path: Path, width: int, height: int, seed: int) -> None:
    """Deterministic RGB gradient written with the stdlib only (no Pillow)."""
    header = struct.pack(">IIBBBBB", width, height, BIT_DEPTH, TRUE_COLOR, 0, 0, 0)
    rows = bytearray()
    for y in range(height):
        rows.append(FILTER_NONE)
        for x in range(width):
            rows.extend(_pixel(x, y, width, height, seed))
    data = (
        PNG_SIGNATURE
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(bytes(rows), 6))
        + _chunk(b"IEND", b"")
    )
    path.write_bytes(data)
