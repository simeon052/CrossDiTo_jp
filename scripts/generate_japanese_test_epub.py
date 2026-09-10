#!/usr/bin/env python3
"""
縦組みの確認用に日本語の EPUB を作る。

縦組みで崩れやすいところを1ページに集めてある:

- 句読点と括弧 (、。「」『』（）) -- 縦組み用の字形に置き換わり、句読点は
  セルの右上に寄る。ここが直っていないと左下に寄って見える
- 小書き仮名 (っゃゅょァィゥ) -- 横組みでは下寄り中央、縦組みでは右上
- 長音符 (ー) -- 縦組みでは縦棒になる
- 欧文と数字の混在 -- 欧文は90度寝かせて流れる
- ルビ -- 縦組みでは列の右側。第一版では描かれないので、消えていることの確認
- 段落の折り返しと禁則 -- 行頭に句読点や閉じ括弧が来ていないか

使い方:
    python scripts/generate_japanese_test_epub.py
    -> test/epubs/test_japanese_vertical.epub
"""

import sys
import zipfile
from pathlib import Path

if any(arg in ("-h", "--help") for arg in sys.argv[1:]):
    print(__doc__.strip())
    sys.exit(0)

OUTPUT = Path(__file__).parent.parent / "test" / "epubs" / "test_japanese_vertical.epub"

CONTAINER = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

# page-progression-direction="rtl" は縦組みの日本語書籍が持つ印。いまの実装は
# 読んでいないが、将来「自動」を足すときの検体としてそのまま入れておく。
CONTENT_OPF = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:crossdito-jp-vertical-test</dc:identifier>
    <dc:title>縦組みテスト</dc:title>
    <dc:creator>CrossDiTo_jp</dc:creator>
    <dc:language>ja</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
  </manifest>
  <spine page-progression-direction="rtl">
    <itemref idref="ch1"/>
    <itemref idref="ch2"/>
  </spine>
</package>
"""

NAV = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>目次</title></head>
<body>
<nav epub:type="toc"><ol>
  <li><a href="ch1.xhtml">第一章　組版の確認</a></li>
  <li><a href="ch2.xhtml">第二章　長めの本文</a></li>
</ol></nav>
</body>
</html>
"""

CH1 = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>第一章</title></head>
<body>
<h1>第一章　組版の確認</h1>

<p>句読点と括弧の位置を見る段落である。「かぎ括弧」で囲んだ部分、それから
『二重かぎ括弧』や（丸括弧）が続く。句点は。読点は、それぞれセルの右上に
寄っているだろうか。</p>

<p>小書き仮名の位置を見る。きっかけ、しゃっくり、ちょっと、ふぁ、ヴィ、
シャッター、ジュース、ミョウガ。これらの小さな字が右上に寄っていれば正しい。</p>

<p>長音符の確認。コーヒー、データ、サーバー、メニュー、ページ。縦組みでは
縦棒になる。</p>

<p>欧文と数字の混在。CrossDiTo は ESP32-S3 で動く。2026年9月10日、Flash は
88.4% を使っている。ABC abc 123 のような並びは寝かせて流れる。</p>

<p>ルビの確認。<ruby>漢字<rt>かんじ</rt></ruby>と<ruby>振<rt>ふ</rt></ruby>り
<ruby>仮名<rt>がな</rt></ruby>。縦組みでは親文字の右に、
半分の大きさで振られていれば正しい。</p>
</body>
</html>
"""

CH2 = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>第二章</title></head>
<body>
<h1>第二章　長めの本文</h1>

<p>吾輩は猫である。名前はまだ無い。どこで生れたかとんと見当がつかぬ。
何でも薄暗いじめじめした所でニャーニャー泣いていた事だけは記憶している。
吾輩はここで始めて人間というものを見た。しかもあとで聞くとそれは書生という
人間中で一番獰悪な種族であったそうだ。この書生というのは時々我々を捕えて
煮て食うという話である。</p>

<p>しかしその当時は何という考もなかったから別段恐しいとも思わなかった。
ただ彼の掌に載せられてスーと持ち上げられた時何だかフワフワした感じが
あったばかりである。掌の上で少し落ちついて書生の顔を見たのがいわゆる
人間というものの見始であろう。</p>

<p>この時妙なものだと思った感じが今でも残っている。第一毛をもって装飾され
べきはずの顔がつるつるしてまるで薬缶だ。その後猫にもだいぶ逢ったがこんな
片輪には一度も出会わした事がない。のみならず顔の真中があまりに突起している。
そうしてその穴の中から時々ぷうぷうと煙を吹く。どうも咽せぽくて実に弱った。
これが人間の飲む煙草というものである事はようやくこの頃知った。</p>

<p>行頭禁則の確認をする長い段落を置く。折り返しの位置に句読点や閉じ括弧が
来ないこと、開き括弧が行末に残らないこと。「このような引用」が行をまたいだ
とき、鉤括弧の位置が正しいかどうか。組版がうまくいっていれば、行頭に、や。
が出ることはない。</p>
</body>
</html>
"""


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as z:
        # mimetype は非圧縮で先頭に置く（EPUB の要求）
        z.writestr(
            zipfile.ZipInfo("mimetype"), "application/epub+zip", zipfile.ZIP_STORED
        )
        z.writestr("META-INF/container.xml", CONTAINER)
        z.writestr("OEBPS/content.opf", CONTENT_OPF)
        z.writestr("OEBPS/nav.xhtml", NAV)
        z.writestr("OEBPS/ch1.xhtml", CH1)
        z.writestr("OEBPS/ch2.xhtml", CH2)
    print(f"Generated: {OUTPUT} ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
