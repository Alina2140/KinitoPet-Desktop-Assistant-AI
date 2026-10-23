"""Build a Windows-friendly multi-size .ico with real alpha (32-bit BMP entries).

PNG-only ICO files often show a white plate in the classic \"Change Icon\"
dialog and get stuck in Explorer's icon cache under the same filename.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_PNG = ROOT / "GameAssets" / "icons" / "Icon.png"
OUT_ICO = ROOT / "GameAssets" / "icons" / "Kinito.ico"
OUT_ICO_LEGACY = ROOT / "GameAssets" / "icons" / "Icon.ico"
SIZES = (16, 24, 32, 48, 64, 128, 256)


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _rgba_to_png_bytes(im: Image.Image) -> bytes:
    """Encode RGBA as a simple PNG (for the 256px ICO entry)."""
    im = im.convert("RGBA")
    w, h = im.size
    raw = b""
    px = im.load()
    for y in range(h):
        raw += b"\x00"
        for x in range(w):
            r, g, b, a = px[x, y]
            raw += bytes((r, g, b, a))
    compressed = zlib.compress(raw, 9)
    return b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)),
            _png_chunk(b"IDAT", compressed),
            _png_chunk(b"IEND", b""),
        )
    )


def _rgba_to_bmp_icon_bytes(im: Image.Image) -> bytes:
    """32-bit BGRA XOR bitmap + empty AND mask (Windows ICO entry with alpha)."""
    im = im.convert("RGBA")
    w, h = im.size
    # BITMAPINFOHEADER
    header = struct.pack(
        "<IIIHHIIIIII",
        40,  # biSize
        w,
        h * 2,  # XOR + AND height
        1,  # planes
        32,  # bit count
        0,  # BI_RGB (alpha still honored in ICO 32bpp)
        0,
        0,
        0,
        0,
        0,
    )
    # XOR bitmap: bottom-up BGRA
    px = im.load()
    xor = bytearray()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            r, g, b, a = px[x, y]
            xor += bytes((b, g, r, a))
    # AND mask: 1 bit/pixel, padded to 32-bit rows (unused when alpha present)
    row_bytes = ((w + 31) // 32) * 4
    and_mask = bytes(row_bytes * h)
    return header + bytes(xor) + and_mask


def build_ico(src: Image.Image, sizes: tuple[int, ...] = SIZES) -> bytes:
    entries: list[tuple[int, bytes]] = []
    for size in sizes:
        frame = src.resize((size, size), Image.Resampling.LANCZOS)
        # Keep fully transparent corners after resize.
        px = frame.load()
        for y in range(size):
            for x in range(size):
                r, g, b, a = px[x, y]
                if a < 16:
                    px[x, y] = (0, 0, 0, 0)
        if size >= 256:
            data = _rgba_to_png_bytes(frame)
        else:
            data = _rgba_to_bmp_icon_bytes(frame)
        entries.append((size, data))

    count = len(entries)
    offset = 6 + count * 16
    directory = bytearray(struct.pack("<HHH", 0, 1, count))
    blobs = bytearray()
    for size, data in entries:
        w_byte = 0 if size >= 256 else size
        h_byte = 0 if size >= 256 else size
        directory += struct.pack(
            "<BBBBHHII",
            w_byte,
            h_byte,
            0,
            0,
            1,
            32,
            len(data),
            offset,
        )
        blobs += data
        offset += len(data)
    return bytes(directory) + bytes(blobs)


def main() -> None:
    if not SRC_PNG.is_file():
        raise SystemExit(f"Missing source PNG: {SRC_PNG}")
    src = Image.open(SRC_PNG).convert("RGBA")
    # Sanity: corners must be transparent.
    if src.getpixel((0, 0))[3] > 16:
        raise SystemExit("Icon.png corner is not transparent — aborting.")
    data = build_ico(src)
    OUT_ICO.write_bytes(data)
    OUT_ICO_LEGACY.write_bytes(data)
    print(f"wrote {OUT_ICO} ({len(data)} bytes)")
    print(f"wrote {OUT_ICO_LEGACY} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
