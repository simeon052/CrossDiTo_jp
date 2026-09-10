"""
シミュレータビルド専用: C のソースを C17 で組む。

GCC 15（Ubuntu 26.04 など新しめのディストリ）は C の既定が C23 で、
bool / true / false がキーワードになった。QRCode ライブラリは古い C 向けに
自前で定義しているので、そのままでは通らない。

  .pio/libdeps/.../QRCode/src/qrcode.h:37: typedef unsigned char bool;
  .pio/libdeps/.../QRCode/src/qrcode.h:38: error: expected identifier
                                            or '(' before 'false'

ライブラリ側を書き換えるのではなく、C の言語標準を C23 より前に固定して
避ける。C++ 側（-std=gnu++2a）には触らない。GCC 13 以前では既定が C17 なので
この指定があってもなくても同じ結果になる。

build_flags に -std=gnu17 と書くと C++ の翻訳単位にも渡ってしまうため、
CFLAGS にだけ足している。
"""

Import("env")  # noqa: F821 - SCons injects this at build time

env.Append(CFLAGS=["-std=gnu17"])
