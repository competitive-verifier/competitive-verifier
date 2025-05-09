# competitive-verifier の細かい仕様
{:.no_toc}

* toc
{:toc}

----
- [English Version](document.html)
- [日本語バージョン](document.ja.html)

## 依存関係の解決
### oj-resolve

Online Judge Verification Helper の機能を使って、ソースコードを解析します。


#### 対応している言語
{:.no_toc}

一覧表:

| 言語 | 認識される拡張子 | 属性の指定方法 | 対応機能 (verify / bundle / doc) | ファイル例 |
|---|---|---|---|---|
| C++ | `.cpp` `.hpp` | `// competitive-verifier: [KEY] [VALUE]` <br> `#define [KEY] [VALUE]` (非推奨) | :heavy_check_mark: / :heavy_check_mark: / :heavy_check_mark: | [segment_tree.range_sum_query.cpp](examples/cpp/segment_tree_tests/segment_tree.range_sum_query.cpp) |
| Nim | `.nim` |  `# competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :heavy_check_mark: | - |
| Python 3 | `.py` |  `# competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :heavy_check_mark: | [union_find_yosupo.py](examples/python/union_find.yosupo.py) |
| Haskell | `.hs` |  `-- competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :warning: | - |
| Ruby | `.rb` |  `# competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :warning: | - |
| Go | `.go` | `// competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :warning: | [helloworld_test.go](examples/go/helloworld_test.go) |
| Java | `.java` | `// competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :warning: | [HelloWorld_test.java](examples/java/HelloWorld_test.java) |
| Rust | `.rs` | `// competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :warning: | [itp1-1-a.rs](examples/rust/verification/src/bin/aizu-online-judge-itp1-1-a.rs) |

#### C++ の設定

`config.toml` というファイルを作って以下のように設定を書くと、コンパイラやそのオプションを指定できます。
設定がない場合は、自動でコンパイラ (`g++` と `clang++`) を検出し、おすすめのオプションを用いて実行されます。

``` toml
[[languages.cpp.environments]]
CXX = "g++"

[[languages.cpp.environments]]
CXX = "clang++"
CXXFLAGS = ["-std=c++17", "-Wall", "-g", "-fsanitize=undefined", "-D_GLIBCXX_DEBUG"]
```

-   [`ulimit`](https://linux.die.net/man/3/ulimit) が動作しないような環境では、自分で `CXXFLAGS` を設定する場合はスタックサイズに注意してください。
-   認識される拡張子は `.cpp` `.hpp` `.cc` `.h` のみです。`.c` や `.h++` のような拡張子のファイルや拡張子なしのファイルは認識されないことに注意してください。

#### Nim の設定

`config.toml` というファイルを作って以下のように設定を書くと、コンパイルの際に変換する言語 (例: `c`, `cpp`) やそのオプションを指定できます。
設定がない場合は AtCoder でのオプションに近いおすすめのオプションが指定されます。

``` toml
[[languages.nim.environments]]
compile_to = "c"

[[languages.nim.environments]]
compile_to = "cpp"
NIMFLAGS = ["--warning:on", "--opt:none"]
```

#### Python 3 の設定

設定項目は特にありません。

#### Rust の設定

[binary ターゲット](https://doc.rust-lang.org/cargo/reference/cargo-targets.html#binaries)と [example ターゲット](https://doc.rust-lang.org/cargo/reference/cargo-targets.html#examples) (ただし`crate-type`が指定されているのは除く) の [root source file](https://docs.rs/cargo_metadata/0.12.0/cargo_metadata/struct.Target.html#structfield.src_path) のうち、[`PROBLEM`](#利用可能な属性)が設定されてあるソースファイルがテストファイルだと認識されます。

依存ファイルを列挙する` の `languages.rust.list_dependencies_backend` で変更できます。

- `kind = "none"`

    デフォルトの動作です。
    それぞれのターゲットに関連する `.rs` ファイルはすべてひとまとまりとして扱われ、それぞれのターゲット内のファイルの間の依存関係などについては調べません。

    ```toml
  [languages.rust.list_dependencies_backend]
  kind = "none"
    ```

    - あるターゲットの root source file であるようなソースファイルについては、そのターゲット及びローカルにある依存クレートの `.rs` ファイルすべてを依存ファイルとして扱います。
    - どのターゲットの root source file でもないようなソースファイルについては、自身を含むターゲットの `.rs` ファイルすべてを依存ファイルとして扱います。

- `kind = "cargo-udeps"`

    基本的に `kind = "none"` と同じですが、 `$PATH` 内にある [cargo-udeps](https://github.com/est31/cargo-udeps) を利用します。クレート間の依存関係を解析し、より適切なファイル間の依存関係を求めます。

    ```toml
  [languages.rust.list_dependencies_backend]
  kind = "cargo-udeps"
  toolchain = "nightly-yyyy-mm-dd" # defaults to "nightly"
    ```

#### その他の言語の設定

上記以外の言語でも実行可能です (例: [examples/awk/circle_test.awk](examples/awk/circle_test.awk))。
`config.toml` というファイルを作って、以下のようにコンパイルや実行のためのコマンドを書いてください (例: [config.toml](https://github.com/competitive-verifier/competitive-verifier/blob/HEAD/examples/config.toml))。
`execute` のフィールドは必須で、その他は省略可能です。

``` toml
[languages.awk]
compile = "bash -c 'echo hello > {tempdir}/hello'"
execute = "env AWKPATH={basedir} awk -f {path}"
bundle = "false"
list_dependencies = "sed 's/^@include \"\\(.*\\)\"$/\\1/ ; t ; d' {path}"
```

**置換される文字列**

|置換元|置換後|
|:---|:----|
|`{basedir}`|実行時のワーキングディレクトリ|
|`{path}`|対象ファイルのパス (`{basedir}`からの相対パス)|
|`{dir}`|対象ファイルがあるディレクトリのパス (`{basedir}`からの相対パス)|
|`{tempdir}`|一時ディレクトリ|

#### ユニットテストの設定

ユニットテストがある場合は, `UNITTEST` 属性を使うことができます。 [helloworld_test.go]({{ "/examples/go/helloworld_test.go" | relative_url }})

{% raw %}
```go
// competitive-verifier: UNITTEST GOTEST_RESULT

package main

import (
    "testing"
    "./helloworld"
)

func TestHelloWorld(t *testing.T) {
    want:= "Hello World"
    if got := helloworld.GetHelloWorld(); got != want {
        t.Errorf("helloworld.GetHelloWorld() = %v, want %v", got, want)
    }
}
```

``` yml
      - name: go test
        id: go-unittest
        run: go test
        working-directory: examples/go
        continue-on-error: true
        env:
          GO111MODULE: "off"

      - name: oj-resolve
        uses: competitive-verifier/actions/oj-resolve@v2
        with:
          include: examples
          exclude: |
            src
            tests
          output-path: resolved.json
          config: examples/config.toml
        env:
          GOTEST_RESULT: ${{ steps.go-unittest.outcome == 'success' }}
```
{% endraw %}

C++ のように main 関数で実行されるユニットテストがある場合は, `STANDALONE` 属性を使うことができます。 [bit_minus_random_test.cpp]({{ "/examples/cpp/bit_minus_random_test.cpp" | relative_url }})

{% raw %}
```cpp
// competitive-verifier: STANDALONE
#include <iostream>
#include <cassert>
#include <random>
#include "examples/cpp/bit_minus.hpp"
using namespace std;

int main()
{
    mt19937 rnd(random_device{}());
    for (size_t i = 0; i < 100000; i++)
    {
        auto num = rnd();
        cout << num << " " << bit_minus(num) << endl;
        assert(-(int64_t)num == bit_minus(num));
    }
    return 0;
}
```
{% endraw %}

### csharp-resolver: C# の設定

[https://github.com/competitive-verifier/csharp-resolver](competitive-verifier/csharp-resolver) を使います。

## verify 自動実行

### 対応サービス一覧

|サービス名|備考|
|---|---|
| [Library Checker](https://judge.yosupo.jp/) | |
| [Aizu Online Judge](https://onlinejudge.u-aizu.ac.jp/home) | |
| [AtCoder](https://atcoder.jp) | 環境変数 `DROPBOX_TOKEN` の設定が必要です。token の値は `$ oj d --system https://atcoder.jp/contests/agc001/tasks/agc001_a` として表示されるヒントに従って取得してください。 |
| [yukicoder](https://yukicoder.me) | 環境変数 `YUKICODER_TOKEN` の設定が必要です。[ヘルプ - yukicoder](https://yukicoder.me/help) の「ログインしてないと使えない機能をAPIとして使いたい」の節や [暗号化されたシークレットの作成と利用 - GitHub ヘルプ](https://help.github.com/ja/actions/configuring-and-managing-workflows/creating-and-storing-encrypted-secrets#creating-encrypted-secrets) 参考にして設定してください。 |

これらの他サービスはテストケースを利用できる形で公開してくれていないため利用できません。

### 利用可能な属性

|変数名|説明|備考|
|---|---|---|
| `PROBLEM` | 提出する問題の URL を指定します | |
| `STANDALONE` | main 関数で実行されるユニットテストファイルに指定します | |
| `ERROR` | 許容誤差を指定します | |
| `TLE` | TLE までの秒数を指定します | |
| `UNITTEST` | ユニットテストが成功したかどうかを表す環境変数を指定します | |
| `TITLE` | ドキュメントのタイトルを指定します | |
| `DISPLAY` | ドキュメントの表示方法を指定します。 | `visible`, `no-index`, `hidden`, `never` |

## ドキュメント生成

### ソースコードのページへの Markdown の埋め込み

リポジトリ内に Markdown ファイルを置いておくと自動で認識されます。
[Front Matter](https://jekyllrb-ja.github.io/docs/front-matter/) 形式で `documentation_of` という項目にファイルを指定しておくと、指定したファイルについての生成されたドキュメント中に、Markdown ファイルの中身が挿入されます。

たとえば、`path/to/segment_tree.hpp` というファイルに説明を Markdown で追加したいときは `for/bar.md` などに次のように書きます。

``` markdown
---
title: Segment Tree
documentation_of: ./path/to/segment_tree.hpp
---

## 説明

このファイルでは、……
```

`documentation_of` 文字列は、`./` あるいは `..` から始まる場合は Markdown ファイルのパスからの相対パスであると認識されます。また、`//` から始まる場合は リポジトリルートからの絶対パスであると認識されます。
また、ディレクトリ区切り文字には `/` を使い、大文字小文字を正しく入力してください。


### トップページへの Markdown の埋め込み

`.competitive-verifier/docs/index.md` というファイルを作って、そこに Markdown で書いてください。

### ローカル実行

`.competitive-verifier/markdown/` ディレクトリ内で以下のようにコマンドを実行すると、生成されたドキュメントが <http://localhost:4000/> から確認できます。

``` console
$ bundle config set --local path .vendor/bundle
$ bundle install
$ bundle exec jekyll serve
```

ただし Ruby の [Bundler](https://bundler.io/) が必要です。
これは Ubuntu であれば `sudo apt install ruby-bundler` などでインストールできます。

### その他の仕様

- ファイル `.competitive-verifier/docs/_config.yml` を作成しておくと、いくつかの修正をした上で出力先ディレクトリにコピーされます。
- ディレクトリ `.competitive-verifier/docs/static/` 以下にファイルを作成しておくと、ドキュメント出力先ディレクトリにそのままコピーされます。
- 互換性のため `.competitive-verifier/` が存在しない場合は `.verify-helper/` を確認します(非推奨)。