#!/usr/bin/env python3
"""
シミュレータを headless で走らせて、実際に描かれた画面を PNG で保存する。

縦組みは「コンパイルが通った」では何も確認できない。字が重なっていないか、
句読点が右上に寄っているか、列が右から左へ積まれているかは、描いた絵を見る
以外に確かめようがない。このスクリプトはそのための最小の仕掛けで、CI から
呼んで成果物として画像を持ち帰ることを想定している。

やること:
  1. 隔離した fs_（疑似SDカード）を用意する
  2. 日本語フォント（.cpfont）を配置する
  3. 組み方向などを設定ファイルに書く
  4. 入力スクリプトで本を開き、決められた時刻にスクリーンショットを撮る

使い方:
    python scripts/run_simulator_screenshots.py --out shots/
    python scripts/run_simulator_screenshots.py --horizontal --out shots-h/
    python scripts/run_simulator_screenshots.py --no-build --font-dir <既存の.cpfont置き場>

フォントは既定で crosspoint-jp のリリース資産から取ってくる（FONT_MANIFEST_URL
と同じ配布元）。ネットワークが無い環境では --font-dir で手元のものを指す。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOOK = ROOT / "test" / "epubs" / "test_japanese_vertical.epub"

# UIのCJKフォールバックが要求するサイズ（8/10/12）と、本文用のサイズ。
# SdCardFontSystem.cpp の kUiFontSizes と対。
FONT_FAMILY = "BIZUDGothic"
FONT_SIZES = (8, 10, 12, 14, 16, 18)
FONT_BASE_URL = "https://github.com/zrn-ns/crosspoint-jp/releases/download/sd-fonts/"

# 起動からの経過ミリ秒。シミュレータは実時間で動くので、本の読み込みと
# 組版が終わるだけの余裕を見て撮る。
SHOT_SCHEDULE_MS = (6000, 9000, 12000)


def build_simulator(env: str) -> None:
    print(f"Building {env} ...", flush=True)
    subprocess.run(["pio", "run", "-e", env], cwd=ROOT, check=True)


def program_path(env: str) -> Path:
    return ROOT / ".pio" / "build" / env / "program"


def fetch_fonts(dest: Path, font_dir: Path | None) -> None:
    """本文用の .cpfont を fs_/.fonts/<family>/ に置く。"""
    family_dir = dest / ".fonts" / FONT_FAMILY
    family_dir.mkdir(parents=True, exist_ok=True)

    for size in FONT_SIZES:
        name = f"{FONT_FAMILY}_{size}.cpfont"
        target = family_dir / name
        if font_dir is not None:
            source = font_dir / name
            if not source.exists():
                raise SystemExit(f"font not found: {source}")
            shutil.copy2(source, target)
            continue
        url = FONT_BASE_URL + name
        print(f"  downloading {name} ...", flush=True)
        with urllib.request.urlopen(url, timeout=120) as response:
            target.write_bytes(response.read())
    print(f"Fonts ready in {family_dir}", flush=True)


def write_settings(dest: Path, vertical: bool) -> None:
    """縦組み＋日本語フォントの設定を書く。

    設定は CrossPointSettings::toJson() が書くのと同じ平たい JSON。ここでは
    確認に要るキーだけ書き、残りは firmware 側の既定値に任せる。
    """
    settings_dir = dest / ".crosspoint"
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings = {
        "sdFontFamilyName": FONT_FAMILY,
        "fontSize": 16,
        "writingMode": 1 if vertical else 0,
        "verticalCharSpacing": 0,
        "language": "JA",
        # 読みやすさに関係しない要素は落として、本文だけを見えるようにする。
        "bionicReading": 0,
        "guideReading": 0,
    }
    path = settings_dir / "crossink-settings.json"
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Settings written: {path}", flush=True)


def prepare_fs(root: Path, book: Path, vertical: bool, font_dir: Path | None) -> str:
    fs_root = root / "fs_"
    if fs_root.exists():
        shutil.rmtree(fs_root)
    books = fs_root / "books"
    books.mkdir(parents=True, exist_ok=True)
    shutil.copy2(book, books / book.name)
    fetch_fonts(fs_root, font_dir)
    write_settings(fs_root, vertical)
    return f"/books/{book.name}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="simulator-shots", help="PNG の出力先")
    parser.add_argument("--book", default=str(DEFAULT_BOOK))
    parser.add_argument("--env", default="x4-pro-simulator")
    parser.add_argument("--horizontal", action="store_true", help="横組みで撮る（比較用）")
    parser.add_argument("--no-build", dest="build", action="store_false")
    parser.add_argument("--font-dir", default=None, help="ダウンロードせず既存の .cpfont を使う")
    parser.add_argument("--timeout", type=int, default=90)
    parser.set_defaults(build=True)
    args = parser.parse_args()

    book = Path(args.book).resolve()
    if not book.exists():
        print(f"book not found: {book}", file=sys.stderr)
        return 2

    if args.build:
        build_simulator(args.env)

    program = program_path(args.env)
    if not program.exists():
        print(f"simulator binary not found: {program}", file=sys.stderr)
        return 2

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    run_root = out_dir / "run"
    run_root.mkdir(exist_ok=True)

    vertical = not args.horizontal
    book_path = prepare_fs(run_root, book, vertical, Path(args.font_dir) if args.font_dir else None)

    # シミュレータは SDL_SaveBMP で書く（PNG ではない）。見るときに扱いやすい
    # ように、撮ったあとで PNG へ変換する（Pillow があれば）。
    suffix = "vertical" if vertical else "horizontal"
    shots = [(ms, out_dir / f"{suffix}-{i + 1}.bmp") for i, ms in enumerate(SHOT_SCHEDULE_MS)]
    schedule = ";".join(f"{ms}:{path}" for ms, path in shots)

    # ホーム画面から本を開き、数ページ送ってから終了する。CONFIRM は
    # 「最近読んだ本 / ファイル一覧」の選択に使う。
    last_ms = SHOT_SCHEDULE_MS[-1]
    input_script = ";".join(
        [
            "2500:DOWN",
            "3000:CONFIRM",
            "7000:DOWN",
            "10000:DOWN",
            f"{last_ms + 1500}:QUIT",
        ]
    )

    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = env.get("SDL_VIDEODRIVER", "dummy")
    env["CROSSPOINT_SIM_SD"] = str(run_root / "fs_")
    env["CROSSPOINT_SIM_SCREENSHOTS"] = schedule
    env["CROSSPOINT_SIM_INPUT_SCRIPT"] = input_script
    env["CROSSINK_SIMULATOR_SMOKE_BOOK"] = book_path

    print(f"Running simulator ({suffix}) ...", flush=True)
    proc = subprocess.run(
        [str(program)],
        cwd=run_root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=args.timeout,
    )
    print(proc.stdout, end="")

    produced = [path for _, path in shots if path.exists()]
    for path in produced:
        print(f"screenshot: {path} ({path.stat().st_size} bytes)")
        convert_to_png(path)

    if not produced:
        print("No screenshots were produced.", file=sys.stderr)
        print("The simulator may not have reached the reader; check the log above.", file=sys.stderr)
        return 1
    return 0


def convert_to_png(bmp: Path) -> None:
    try:
        from PIL import Image
    except ImportError:
        return
    try:
        with Image.open(bmp) as image:
            image.save(bmp.with_suffix(".png"))
    except Exception as exc:  # 変換できなくても BMP は残っているので致命ではない
        print(f"  (PNG conversion skipped for {bmp.name}: {exc})")


if __name__ == "__main__":
    sys.exit(main())
