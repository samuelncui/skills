#!/usr/bin/env python3
"""Regenerate the original paired-layout diagram using only Python's stdlib."""
from pathlib import Path
import struct
import zlib


def draw():
    width, height = 900, 260
    pixels = bytearray(bytes((251, 250, 247)) * width * height)

    def rectangle(left, top, right, bottom, color):
        for y in range(top, bottom):
            for x in range(left, right):
                start = 3 * (y * width + x)
                pixels[start:start + 3] = bytes(color)

    green, blue, arrow = (18, 105, 94), (48, 87, 137), (91, 103, 110)
    rectangle(35, 70, 200, 190, green)
    rectangle(220, 70, 385, 190, blue)
    rectangle(420, 124, 540, 136, arrow)
    for offset in range(30):
        rectangle(530 + offset, 100 + offset, 532 + offset, 160 - offset, arrow)
    rectangle(620, 35, 855, 120, green)
    rectangle(620, 140, 855, 225, blue)
    scanlines = b"".join(b"\0" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xffffffff)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(scanlines, 9)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    path = Path(__file__).parent / "images" / "pairs.png"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(draw())
    print(path.name)
