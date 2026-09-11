# 日本語対応（CrossDiTo_jp）

このフォークで CrossDiTo を日本語で使えるようにするための作業メモ。

## 現状

| 段階 | 内容 | 状態 |
|---|---|---|
| 1 | 日本語UI（翻訳・フォント入手経路） | **実装済み（実機未検証）** |
| 2 | 縦書き（vertical-rl） | 未着手 |
| 3 | 縦書き/横書きの独立設定、右→左のページ送り | 未着手 |
| 4 | 青空文庫連携、TXT→EPUB 変換 | 未着手 |

## Stage 1 でやったこと

### 日本語UI

`lib/I18n/translations/japanese.yaml` を追加した（774キー中 765キーを翻訳、
残り9キーは日付書式のサンプル文字列なので英語のまま）。既訳のうち 310キーは
[crosspoint-jp](https://github.com/zrn-ns/crosspoint-jp) から流用している。

`scripts/gen_i18n.py` は `lib/I18n/translations/*.yaml` を全部読むので、
ファイルを置くだけで言語一覧に「日本語」が出る。ビルド設定の変更は不要。

- `_language_code: "JA"` / `_order: "27"`（既存の最大は 28、27 が空いていた）
- 文字列データは約 20KB 増える

### 日本語フォントの入手経路

CrossDiTo が既定で参照する CrossInk のフォント配信バケットには、**日本語フォントが
1つも入っていない**（Latin 系のみ）。そのため `platformio.ini` の `[base]` で
`FONT_MANIFEST_URL` を crosspoint-jp のマニフェストへ向けた。

```
https://github.com/zrn-ns/crosspoint-jp/releases/download/sd-fonts/fonts.json
```

- BIZ UDGothic / BIZ UD明朝 / NotoSansJP / NotoSerifJP を収録
- 配布されている `.cpfont` は **v5**（縦書き用の vert セクションを持つ）。
  CrossDiTo の読み込みは v4 固定だったので、v4–v5 を受け付けるようにした（後述）
- 8 / 10 / 12 / 14 / 16 / 18 pt を収録。**8/10/12pt** は UI の CJK フォールバックが
  要求するサイズ（`src/SdCardFontSystem.cpp` の `kUiFontSizes`）なので、これが
  無いとメニューの日本語が豆腐になる

> **注意:** 現状は他プロジェクトのリリース資産に依存している。安定運用するなら
> このフォークのリリースへフォントをミラーして、URL を差し替えること。

### .cpfont v5 の受け入れ

配布されている日本語フォントは **v5** で、CrossDiTo の読み込みは v4 固定だった
ため、そのままではマニフェストを差し替えても `Unsupported version: 5` で弾かれる。
`SdCardFont::load()` が v4–v5 を受け付けるようにした。

v5 と v4 の差は次の1点だけで、v4 の読み方をしても他のオフセットはすべて一致する。

- スタイルTOCの offset 28（v4 では予約領域だった4バイト）に、縦書き用の
  vert セクションの位置が入る
- ファイル末尾にその vert セクションが付く
- グローバルヘッダ32バイト / TOCエントリ32バイトという寸法は v4 と同じ

`CPFONT_VERSION` は配信URLに埋め込む版番号なので 4 のまま据え置き、受け入れ上限を
`CPFONT_VERSION_MAX_SUPPORTED` として別に持たせている。

vert セクション（OpenTypeの縦書き代替字形）は Stage 2 で使う。v4 の読み方では
無視されるだけなので、Stage 1 の時点では実害も利得もない。

### 日本語が表示される仕組み（既存機能）

CrossDiTo（＝CrossPoint 1.5 系）には既に CJK まわりの土台がある。Stage 1 で
新規に実装したものではない。

- CJK の行分割: `utf8IsCjkBreakable()`
- 禁則処理: `isNoBreakBeforeCjkPunctuation()` / `isNoBreakAfterCjkPunctuation()`
  （`lib/Epub/Epub/ParsedText.cpp`）
- ルビ（振り仮名）: `TextBlock` の `rubyTexts` + `EpdFontFamily::RUBY_CONTINUE`
- **UIのCJKフォールバック**: 選んだ本文用SDフォントが CJK を含む場合
  （U+4E00 / U+3042 / U+30A2 / U+AC00 で判定）、同じフォントの 8/10/12pt を
  読み込んでUIフォントのフォールバックに登録する
  （`src/SdCardFontSystem.cpp:245` 付近）

つまり **本文フォントに日本語フォントを選べば、メニューの日本語も出る**。

## 使い方（Stage 1 時点）

1. 設定 → フォントを管理 から `BIZUDGothic` などをダウンロード
2. 本文フォントにそのフォントを選択
3. 設定 → 言語 で「日本語」を選択

## 未対応

- **縦書きは未対応**（Stage 2）。`vertical-rl` / `writing-mode` を扱うコードは
  CrossDiTo 本体に存在しない
- 日付書式のサンプル表示（`STR_DATE_FORMAT_*`）は英語のまま。実際の描画も英語の
  月名を出すため、ラベルだけ和訳すると表示と食い違う
- 青空文庫のTXT形式には未対応
