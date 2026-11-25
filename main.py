#!/usr/bin/env python3
"""news-image-20261125 entry (Python 3.13, standard library only).

The entry's image is the entry.png beside this file: a one-page newspaper
front page summing up the world's news of Wednesday 25 November 2026
(lead: Ukraine's drone strikes on Russian ships in the Gulf of Finland and
off Benghazi; panels: COP31 collapses, Huawei found guilty, CIA hit by a
cyberattack, Nvidia's wild ride, Houthis hit Riyadh's tallest tower, new US
tariffs loom; briefs: Australia's apology to LGBTQ veterans, WHO's Ebola
evacuation in DR Congo, Gaza death toll 74,746).

The program verifies the PNG (signature, IHDR size, per-chunk CRCs and the
decompressed image data) and copies it to /output/entry.png. Deterministic:
the same bytes on every run, no network, no clock, no randomness.

Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
OUT = os.path.join(OUT_DIR, "entry.png")

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1048576
EXPECT_W, EXPECT_H = 1024, 1024


def verify_png(data):
    """Check the PNG is whole: signature, IHDR size, chunk CRCs, image data."""
    if len(data) < 8 or data[:8] != PNG_SIGNATURE:
        raise ValueError("entry.png is not a PNG file")
    if len(data) > MAX_BYTES:
        raise ValueError("entry.png is %d bytes, over the 1 MiB limit" % len(data))
    pos = 8
    width = height = None
    bit_depth = color_type = None
    idat = bytearray()
    seen_iend = False
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        end = pos + 8 + length + 4
        if end > len(data):
            raise ValueError("truncated PNG chunk %r" % ctype)
        chunk = data[pos + 8:end - 4]
        crc_stored = struct.unpack(">I", data[end - 4:end])[0]
        crc_actual = zlib.crc32(ctype)
        crc_actual = zlib.crc32(chunk, crc_actual)
        if crc_actual != crc_stored:
            raise ValueError("bad CRC in PNG chunk %r" % ctype)
        if ctype == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            seen_iend = True
            break
        pos = end
    if width is None:
        raise ValueError("entry.png has no IHDR chunk")
    if (width, height) != (EXPECT_W, EXPECT_H):
        raise ValueError("entry.png is %dx%d, expected 1024x1024" % (width, height))
    if not seen_iend:
        raise ValueError("entry.png has no IEND chunk")
    # The image data must decompress to exactly one filter byte per row plus
    # the pixels the header describes (RGB, 8 bit: 3 bytes per pixel).
    raw = zlib.decompress(bytes(idat))
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    expect_raw = height * (1 + width * channels)
    if bit_depth != 8 or len(raw) != expect_raw:
        raise ValueError("entry.png image data does not match its header")
    return width, height


def main():
    with open(SRC, "rb") as f:
        data = f.read()
    width, height = verify_png(data)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, %dx%d)" % (OUT, len(data), width, height))
    return 0


if __name__ == "__main__":
    sys.exit(main())
