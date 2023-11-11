# Design Doc

## 目的

`competitive-verifier` は `oj-verify` [online-judge-tools/verification-helper](https://github.com/online-judge-tools/verification-helper) の改善版となるのを目的として開発された。

## Overview

以下のサブコマンドを持つ

    verify              Verify library
    docs                Create documents
    download            Download problems
    merge-input         Merge verify_files.json
    merge-result        Merge result of `verify`
    check               Check result of `verify`
    oj-resolve          Create verify_files json using `oj-verify`
    migrate             Migration from verification-helper(`oj-verify`) project

1. oj-resolve: ソースコードの解析
    - いきなり多言語対応するのは労力が大きいので `oj-verify` のものを改造して使用。
    - 個別の新規開発するモチベーションは低いので機能追加予定はなし。
1. verify: ドキュメント生成
    - resolve の結果から verify を実行する
    - 並列実行用の引数を用意しておく
1. docs: ドキュメント生成
    - resolve, verify の結果からドキュメントを生成する
    - [Jekyll](https://jekyllrb-ja.github.io/) 形式で出力する
1. check: verify の結果が成功かどうかをチェックする
    - verify を並列実行した際にはすべてを終えてからチェックすることを想定している
1. download: 問題のダウンロード
    - 開発時の利便性を考えて verify から問題のダウンロード部分だけ切り出して実行
1. merge-input, merge-result: 並列実行で別々に使用したファイルをマージする
1. migrate: `oj-verify` からのマイグレーション

## 設計思想
### oj-verify の課題

2022年現在、[oj-verify](https://github.com/online-judge-tools/verification-helper) は開発停止となっているため、機能改善が見込めない状態となっている。

また、oj-verify には下記のような課題があった。また、透過的な実装をする

- resolve, verify, documentation などの機能がひとまとめになっているため開発しづらい。
- 言語ごとの実装がコマンドに埋め込まれており、外部から機能を注入することが難しい。
  - そのため C# は事実上まともに使用することができない。
- [Library checker](https://github.com/yosupo06/library-checker-problems) の問題生成などで実行に非常に時間がかかる。
  - この対策として verify の結果を毎回コミットするため log に非本質的情報が溜まってしまう。
- ユニットテストとの統合が困難。
  - 特に .NET や Go などの `main()` と無関係なユニットテストを持つ言語で非常に厳しい。

これらのなかには [verification-helper#116](https://github.com/online-judge-tools/verification-helper/issues/116) のように透過的な実装を目指してあえてそうなっているものもある。


### competitive-verifier の設計

-  **決定論的** かつ **冪等** であること
  - 言語ごとの独自機能を実行できるようにする効果がある。
  - 入力を元に実行することで決定論的にしたいという目的もある。
  - 内部で状態を持たないので冪等性も担保する。
  - この実現のため resolve, verify, docs などをサブコマンドとして独立して実行するよう制限した。
    - `oj-verify` ではdocs コマンドはあるものの、実質 all コマンドが必須だった。
- 異なるマシンで並列実行できるようにする
  - GitHub Actions の job を複数実行する状況を想定
  - `oj-verify` では20分かかっても終わらないライブラリでも20並列で実行することで高速に完了する。


## 更新日
- 2022-12-12: 初版