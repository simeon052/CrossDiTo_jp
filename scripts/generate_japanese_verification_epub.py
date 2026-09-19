"""実機で縦組みの修正点を確認するための EPUB を作る。

test/epubs/test_japanese_vertical.epub は CI のスクリーンショット用の固定物で、
勝手に変えると差分が出る。こちらは実機確認用に分けてある。

各章の見出しに「何を見るか」と「正しい状態」を書いてあるので、ページを送り
ながら突き合わせればよい。

  python scripts/generate_japanese_verification_epub.py
"""

import zipfile
from pathlib import Path

OUTPUT = Path(__file__).parent.parent / "test" / "epubs" / "verify_japanese_vertical.epub"

CONTAINER = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

CHAPTERS = [
    ("ch1", "1 欧文と数字の向き"),
    ("ch2", "2 括弧と記号の回転"),
    ("ch3", "3 罫線"),
    ("ch4", "4 ルビと文字装飾"),
    ("ch5", "5 記号の収録確認"),
    ("ch6", "6 組版の基本"),
]

CONTENT_OPF = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:crossdito-jp-vertical-verify</dc:identifier>
    <dc:title>縦組み確認</dc:title>
    <dc:creator>CrossDiTo_jp</dc:creator>
    <dc:language>ja</dc:language>
  </metadata>
  <manifest>
%(items)s    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
  </manifest>
  <spine page-progression-direction="rtl">
%(spine)s  </spine>
</package>
""" % {
    "items": "".join(
        f'    <item id="{cid}" href="{cid}.xhtml" media-type="application/xhtml+xml"/>\n'
        for cid, _ in CHAPTERS
    ),
    "spine": "".join(f'    <itemref idref="{cid}"/>\n' for cid, _ in CHAPTERS),
}

NAV = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>目次</title></head>
<body>
<nav epub:type="toc"><ol>
%s</ol></nav>
</body>
</html>
""" % "".join(f'  <li><a href="{cid}.xhtml">{title}</a></li>\n' for cid, title in CHAPTERS)


def page(cid: str, title: str, body: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml">\n'
        f"<head><title>{title}</title></head>\n"
        f"<body>\n<h1>{title}</h1>\n{body}</body>\n</html>\n"
    )


CH1 = page("ch1", "1 欧文と数字の向き", """
<p><b>見るところ</b>　数字と英単語が時計回りに寝て、上から下へ読めること。
字の上が右を向いていれば正しい。左を向いていたら回転の向きが逆。</p>

<p>100点満点中5000点くらいだ。嘘、100万点くらい。</p>

<p>CrossDiTo は ESP32-S3 で動く。2026年9月10日、Flash は 88.4% を使っている。
ABC abc 123 のような並びは寝かせて流れる。</p>

<p><b>並び順の確認</b>　次が ABCDEF と読めれば正しい。FEDCBA と読めたら逆順。</p>

<p>ABCDEF</p>

<p><b>中心のずれ</b>　次の行で、寝かせた数字が上下の全角文字と同じ軸に載っているか。
右や左へ寄っていたら中心がずれている。</p>

<p>あいうえお123かきくけこ</p>

<p>ああああ42ああああ</p>
""")

CH2 = page("ch2", "2 括弧と記号の回転", """
<p><b>見るところ</b>　括弧と波線が90度回って、縦向きになっていること。
横向きのまま残っていたら回転していない。</p>

<p>山括弧　〈やまかっこ〉と《二重山括弧》</p>

<p>全角不等号　＜タイトル一覧＞</p>

<p>丸括弧　（まるかっこ）</p>

<p>角括弧　［かくかっこ］と【すみつきかっこ】と〔きっこう〕</p>

<p>波ダッシュ　これ〜これ　と　これ～これ</p>

<p>ダッシュ　——ここで切れる——</p>

<p>三点リーダ　……そして……</p>

<p>長音符　コーヒー、データ、サーバー</p>

<p>その他　全角ハイフン－と全角イコール＝</p>

<p>引用符　“英語の二重”と‘英語の単一’</p>

<p>引用符　＂全角二重＂と＇全角単一＇</p>

<p>引用符　"ASCII二重"と'ASCII単一'</p>

<p>引用符　〝縦書き用〟</p>

<p><b>回らない字</b>　次は回らないのが正しい。句読点は右上に寄る。</p>

<p>、。！？ここまで</p>
""")

CH3 = page("ch3", "3 罫線", """
<p><b>見るところ</b>　次の罫線が<b>縦向き</b>に出ること。横向きの線が列を横切って
いたら、座標変換が効いていない。</p>

<hr/>

<p>罫線の上下（画面では左右）に、この段落が分かれて出ていれば位置も正しい。</p>

<hr/>

<p>2本目の罫線のあと。</p>
""")

CH4 = page("ch4", "4 ルビと文字装飾", """
<p><b>見るところ</b>　ルビが親文字の<b>右</b>に半分の大きさで出ること。
傍線は列の<b>左</b>、打ち消し線は列の<b>中央</b>。</p>

<p><ruby>漢字<rt>かんじ</rt></ruby>と<ruby>振<rt>ふ</rt></ruby>り<ruby>仮名<rt>がな</rt></ruby>。
<ruby>薔薇<rt>ばら</rt></ruby>、<ruby>檸檬<rt>れもん</rt></ruby>、
<ruby>躊躇<rt>ちゅうちょ</rt></ruby>。</p>

<p><u>ここが傍線</u>で、縦組みでは列の左に引かれる。</p>

<p><s>ここが打ち消し線</s>で、こちらは列の中央を通る。</p>

<p>ルビの付いた語に<u><ruby>傍線<rt>ぼうせん</rt></ruby></u>を重ねた場合。
ルビが右、傍線が左に分かれていれば正しい。</p>
""")

CH5 = page("ch5", "5 記号の収録確認", """
<p><b>見るところ</b>　次の記号が出るか。<b>◆（黒い菱形）になっていたら、その字は
フォントに入っていない。</b>配信されている日本語フォントでは全部 ◆ になる。
自分で焼いたフォントなら出る。</p>

<p>矢印　→ ← ↑ ↓</p>

<p>図形　■ □ ● ○ ◇ ▲ △</p>

<p>星と音符　★ ☆ ♪</p>

<p>単位と数式　℃ ∞ ≠ ≦ ±</p>

<p>囲み数字　① ② ③</p>

<p>罫線素片　─ │</p>

<p><b>こちらは配信フォントでも出る</b>　取り違えないこと。</p>

<p>※ … ‥ — ― × ° § 〒 々 〆 〇</p>

<p><b>空白になる字</b>　◆ ではなく何も出ない場合、収録リストには入っているが
元のフォントに字形が無い。◆ より気づきにくい。</p>
""")

CH6 = page("ch6", "6 組版の基本", """
<p><b>見るところ</b>　列が右から左へ進み、句読点と括弧が縦用の形になること。</p>

<p>句読点と括弧の位置を見る段落である。「かぎ括弧」で囲んだ部分、それから
『二重かぎ括弧』や（丸括弧）が続く。句点は。読点は、それぞれセルの右上に
寄っているだろうか。</p>

<p>小書き仮名の位置を見る。きっかけ、しゃっくり、ちょっと、ふぁ、ヴィ、
シャッター、ジュース、ミョウガ。これらの小さな字が右上に寄っていれば正しい。</p>

<p><b>禁則</b>　折り返しの行頭に句読点や閉じ括弧が来ないこと。次の段落を
いろいろな字間・行間で見ると分かりやすい。</p>

<p>あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほ、まみむめも
やゆよらりるれろわをん。「あいうえお」かきくけこ（さしすせそ）たちつてと。
なにぬねのはひふへほまみむめもやゆよらりるれろ、わをん。</p>

<p><b>字間の効き</b>　設定 → 読書 → ページレイアウト → 縦書きの字間 を
0 と 30 で見比べる。字の間隔が広がり、<b>ページ番号の分母も変わる</b>。
分母が変わらなければ効いていない。</p>
""")

PAGES = {"ch1": CH1, "ch2": CH2, "ch3": CH3, "ch4": CH4, "ch5": CH5, "ch6": CH6}


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as z:
        # mimetype は非圧縮で先頭に置く（EPUB の要求）
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", CONTAINER)
        z.writestr("OEBPS/content.opf", CONTENT_OPF)
        z.writestr("OEBPS/nav.xhtml", NAV)
        for cid, _ in CHAPTERS:
            z.writestr(f"OEBPS/{cid}.xhtml", PAGES[cid])
    print(f"Generated: {OUTPUT} ({OUTPUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
