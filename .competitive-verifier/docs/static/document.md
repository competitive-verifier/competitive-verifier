# The reference of competitive-verifier
{:.no_toc}

* toc
{:toc}

----
- [English Version](document.html)
- [日本語バージョン](document.ja.html)

## Resolving dependencies
### oj-resolve

`oj-resolve` subcommand reslove source code status by Online Judge Verification Helper.

#### Supported languages
{:.no_toc}

Summary:

| Language | Available file extensions | How to specify attributes | Features (verify / bundle / doc) | Example file |
|---|---|---|---|---|
| C++ | `.cpp` `.hpp` | `// competitive-verifier: [KEY] [VALUE]` or `#define [KEY] [VALUE]`(deprecated) | :heavy_check_mark: / :heavy_check_mark: / :heavy_check_mark: | [segment_tree.range_sum_query.test.cpp](https://github.com/online-judge-tools/verification-helper/blob/master/examples/segment_tree.range_sum_query.test.cpp) |
| Nim | `.nim` |  `# competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :heavy_check_mark: | [union_find_tree_yosupo_test.nim](https://github.com/online-judge-tools/verification-helper/blob/master/examples/nim/union_find_tree_yosupo_test.nim) |
| Python 3 | `.py` |  `# competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :heavy_check_mark: | [union_find_yosupo.test.py](https://github.com/online-judge-tools/verification-helper/blob/master/examples/python/union_find_yosupo.test.py) |
| Haskell | `.hs` |  `-- competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :warning: | [HelloWorld.test.hs](https://github.com/online-judge-tools/verification-helper/blob/master/Examples2/Haskell/HelloWorld.test.hs) |
| Ruby | `.rb` |  `# competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :warning: | [hello_world.test.rb](https://github.com/online-judge-tools/verification-helper/blob/master/examples/ruby/hello_world.test.rb) |
| Go | `.go` | `// competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :warning: | [helloworld.test.go](https://github.com/online-judge-tools/verification-helper/blob/master/examples/go/helloworld.test.go) |
| Java | `.java` | `// competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :warning: | [HelloWorld_test.java](https://github.com/online-judge-tools/verification-helper/blob/master/examples/java/HelloWorld_test.java) |
| Rust | `.rs` | `// competitive-verifier: [KEY] [VALUE]` | :heavy_check_mark: / :x: / :warning: | [itp1-1-a.rs](https://github.com/online-judge-tools/verification-helper/blob/master/examples/rust/verification/src/bin/aizu-online-judge-itp1-1-a.rs) |

#### Settings for C++

You can specify compilers and options with writing `config.toml` as below.
If there are no settings, oj-resolve automatically detects compilers (`g++` and `clang++` if exists) and use recommended options.

``` toml
[[languages.cpp.environments]]
CXX = "g++"

[[languages.cpp.environments]]
CXX = "clang++"
CXXFLAGS = ["-std=c++17", "-Wall", "-g", "-fsanitize=undefined", "-D_GLIBCXX_DEBUG"]
```

-   If you use environments which [`ulimit`](https://linux.die.net/man/3/ulimit) doesn't work on, and if you want to set `CXXFLAGS` by yourself, please be careful about the stack size.
-   The supported extensions are `.cpp`, `.hpp`, `.cc`, and `.h`. Please note that files with other extensions like `.c` `.h++` and files without extensions are not recognized.

#### Settings for Nim

You can specify options and targets (e.g. `c` `cpp`) with writing `config.toml` as below.
If there is no settings, oj-resolve automatically use recommended options similar to options on AtCoder.

``` toml
[[languages.nim.environments]]
compile_to = "c"

[[languages.nim.environments]]
compile_to = "cpp"
NIMFLAGS = ["--warning:on", "--opt:none"]
```

#### Settings for Python 3

There is no config now.

#### Settings for Rust

`oj-verify` uses [root source files](https://docs.rs/cargo_metadata/0.12.0/cargo_metadata/struct.Target.html#structfield.src_path) of [binary targets](https://doc.rust-lang.org/cargo/reference/cargo-targets.html#binaries) or [example targets](https://doc.rust-lang.org/cargo/reference/cargo-targets.html#examples) (excluding targets which `crate-type` is specified) which have the [`PROBLEM`](#available-macro-definitions) attribute

You can customize the method to list depending files with `languages.rust.list_dependencies_backend` of `config.toml`.

- `kind = "none"`

    This is the default behavoir.
    For each target, all `.rs` files in the target is treated as a block. The dependency relationship of files in each target are not analyzed.

    ```toml
    [languages.rust.list_dependencies_backend]
    kind = "none"
    ```

    - For a file which is a root source file of a target, the file depends all `.rs` files in its target and all depending local crates.
    - For a file which is not a root source file of any targets, the file depends all `.rs` files in its target.

- `kind = "cargo-udeps"`

    This method is similar to `kind = "none"`, but uses [cargo-udeps](https://github.com/est31/cargo-udeps) in `$PATH` to narrow down dependencies. It computes the dependency relationship of files using the dependencies relationship between crates.

    ```toml
    [languages.rust.list_dependencies_backend]
    kind = "cargo-udeps"
    toolchain = "nightly-yyyy-mm-dd" # defaults to "nightly"
    ```

#### Settings for other languages

You can use languages other than above (e.g. AWK [examples/awk/circle.test.awk](https://github.com/online-judge-tools/verification-helper/blob/master/examples/awk/circle.test.awk)). Please write commands to compile and execute in the config file `config.toml` (e.g. [config.toml](https://github.com/competitive-verifier/competitive-verifier/blob/HEAD/examples/config.toml)).
`execute` field are required, and other fields are optional.

``` toml
[languages.awk]
compile = "bash -c 'echo hello > {tempdir}/hello'"
execute = "env AWKPATH={basedir} awk -f {path}"
bundle = "false"
list_dependencies = "sed 's/^@include \"\\(.*\\)\"$/\\1/ ; t ; d' {path}"
```

**Replacement**

|Config|Actual|
|:---|:----|
|`{basedir}`|The working directory.|
|`{path}`| The relative path to `{basedir}` of the file to execute. |
|`{dir}`| The relative path to `{basedir}` of the directory which contains file to execute. |
|`{tempdir}`|The temporary directory.|

#### Unit test

If you have unit tests, you can use `UNITTEST` attribute. [helloworld_test.go]({{ "/examples/go/helloworld_test.go" | relative_url }})

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

```yml
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

specify in the unit test file executed by the main function

If you have unit tests executed by the main function like C++, you can use `STANDALONE` attribute. [bit_minus_random_test.cpp]({{ "/examples/cpp/bit_minus_random_test.cpp" | relative_url }})

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

### csharp-resolver: C# settings

Use [https://github.com/competitive-verifier/csharp-resolver](competitive-verifier/csharp-resolver).


## Automating the verification

### Available judging platforms

|Name|Remarks|
|---|---|
| [Library Checker](https://judge.yosupo.jp/) | |
| [Aizu Online Judge](https://onlinejudge.u-aizu.ac.jp/home) | |
| [AtCoder](https://atcoder.jp) | You must set the `DROPBOX_TOKEN` environment variable. You can obtain the token by following the HINT message shown by `$ oj d --system https://atcoder.jp/contests/agc001/tasks/agc001_a`. |
| [yukicoder](https://yukicoder.me) | You must set the `YUKICODER_TOKEN` environment variable. See 「ログインしてないと使えない機能をAPIとして使いたい」 in [ヘルプ - yukicoder](https://yukicoder.me/help) and [Creating and using encrypted secrets - GitHub Help](https://help.github.com/en/actions/configuring-and-managing-workflows/creating-and-storing-encrypted-secrets). |

Other judging platforms do not currently publish the test cases in usable forms, and so are not currently supported.

### Available macro definitions

|Macro name|Description|Remarks|
|---|---|---|
| `PROBLEM` | specify the URL of the problem to submit | |
| `STANDALONE` | specify in the unit test file executed by the main function | |
| `ERROR` | specify the absolute or relative error to be considered as correct | |
| `TLE` | specify the TLE time in seconds | |
| `UNITTEST` | specify the environment variable which represents unit test status  | |
| `TITLE` | specify the title of source  | |
| `DISPLAY` | specify the document output mode | `visible`, `no-index`, `hidden`, `never` |

## Generating Documentation

### Embedding Markdown to pages for source codes

Markdown files in the repository are automatically recognized.
When the `documentation_of` field in [Front Matter](https://jekyllrb-ja.github.io/docs/front-matter/) specifies a source code file, the content of Markdown file is inserted into the generated document page of specified code.

For example, to add description to a document of a file `path/to/segment_tree.hpp`, make a Markdown file like `foo/bar.md` and write as the following in the file.

```
---
title: Segment Tree
documentation_of: ./path/to/segment_tree.hpp
---

## Description

In this file, ...
```markdown

The `documentation_of` string is recognized as a relative path from the Markdown file when the string starts with `./` or `..`.
The `documentation_of` string is recognized as a absolute path from the git root directory when the string starts with `//`.
The path should use `/` as directory separator be case-sensitive.


### Embedding Markdown to the top page

Please make the file `.competitive-verifier/docs/index.md` and write Markdown there.


### Local execution

Executing following commands, you can see generated documents locally at <http://localhost:4000/>.

``` console
$ bundle config set --local path .vendor/bundle
$ bundle install
$ bundle exec jekyll serve
```

To do this, Ruby's [Bundler](https://bundler.io/) is required.
If you are using Ubuntu, you can install this with `sudo apt install ruby-bundler`.


### Others

- The file `.competitive-verifier/docs/_config.yml` is copied into the target directory with some modification.
- Files under the directory `.competitive-verifier/docs/static/` are copied into the target directory directly.
- For compatibility, you can use `.verify-helper/` instead of `.competitive-verifier/`. (deprecated)