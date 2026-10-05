#!/usr/bin/env python3
"""
焼く前に「起動しないイメージ」を弾く。

ESP32-S3 では flash の rodata(DROM) と PSRAM が同じアドレス領域を使うため、
ESP-IDF の sections.ld は rodata の開始位置を「.flash.text のぶんだけ空ける」
形で決めている。

    .flash_rodata_dummy (NOLOAD):
    {
      . = SIZEOF(.flash.text);
      . = ALIGN(_esp_mmu_block_size) + 0x20;
      _rodata_reserved_start = .;
    } > default_rodata_seg

ところがこの領域の原点は 0x3C000020 で、64KB 境界から 0x20 ずれている。
.flash.text が 64KB 境界の直前 0x20 バイトに着地すると、空隙は1ページぶん
足りなくなる。IROM と DROM は MMU のページを分け合うので、DROM の割り当てが
1ページずれ、起動直後に読むイメージヘッダが別の内容になる。

    E (941) cpu_start: Invalid app image header
    abort() was called at PC 0x... (system_early_init)

リンクもビルドも成功し、焼くまで分からない。実際 v1.5.1.10 と v1.5.1.11 を
配布してしまい、実機がブートループに入った。ここで止める。
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

MMU_PAGE = 0x10000
DROM_SEG_ORIGIN = 0x3C000020  # memory.ld の drom0_0_seg
DROM_WINDOW = (0x3C000000, 0x3E000000)
IROM_WINDOW = (0x42000000, 0x42800000)


def segments(image: bytes):
    """ESP32 イメージのセグメント（ロードアドレス, 長さ）を返す。"""
    if not image or image[0] != 0xE9:
        raise SystemExit("not an ESP32 app image (magic != 0xE9)")
    count = image[1]
    offset = 24  # 共通ヘッダ8 + 拡張ヘッダ16
    out = []
    for _ in range(count):
        load, length = struct.unpack("<II", image[offset:offset + 8])
        offset += 8 + length
        out.append((load, length))
    return out


def check(path: Path) -> int:
    image = path.read_bytes()
    irom = drom = None
    for load, length in segments(image):
        if IROM_WINDOW[0] <= load < IROM_WINDOW[1]:
            irom = (load, length)
        elif DROM_WINDOW[0] <= load < DROM_WINDOW[1]:
            drom = (load, length)
    if irom is None or drom is None:
        raise SystemExit(f"{path.name}: could not find both IROM and DROM segments")

    irom_load, irom_len = irom
    drom_load, _ = drom

    # IROM が占める MMU ページ数。ページ内の開始位置（通常 0x20）も含めて数える。
    needed_pages = -(-((irom_load % MMU_PAGE) + irom_len) // MMU_PAGE)
    # rodata の手前に空けてあるぶん＝確保済みページ数。
    reserved_pages = (drom_load - DROM_SEG_ORIGIN) // MMU_PAGE

    slack = reserved_pages * MMU_PAGE - ((irom_load % MMU_PAGE) + irom_len)
    print(f"{path.name}")
    print(f"  IROM  load=0x{irom_load:08X} size={irom_len} (0x{irom_len:X})  -> {needed_pages} pages")
    print(f"  DROM  load=0x{drom_load:08X}  reserved={reserved_pages} pages")
    print(f"  slack {slack} bytes")

    if reserved_pages < needed_pages:
        print(
            f"  NG: IROM needs {needed_pages} MMU pages but only {reserved_pages} are reserved.\n"
            f"      This image boot-loops with 'Invalid app image header'.\n"
            f"      .flash.text landed within 0x20 of a 64KB boundary; nudge the code size\n"
            f"      (see CODE_SIZE_MMU_PAD in src/main.cpp).",
            file=sys.stderr,
        )
        return 1
    print("  OK")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: check_image_mmu_split.py <firmware.bin> [...]", file=sys.stderr)
        return 2
    status = 0
    for arg in sys.argv[1:]:
        status |= check(Path(arg))
    return status


if __name__ == "__main__":
    sys.exit(main())
