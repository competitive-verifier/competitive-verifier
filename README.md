# competitive-verifier

[![Actions Status](https://github.com/competitive-verifier/competitive-verifier/actions/workflows/verify.yml/badge.svg)](https://github.com/competitive-verifier/competitive-verifier/actions) [![GitHub Pages](https://img.shields.io/static/v1?label=GitHub+Pages&message=+&color=brightgreen&logo=github)](https://competitive-verifier.github.io/competitive-verifier)
[![PyPI](https://img.shields.io/pypi/v/competitive-verifier)](https://pypi.org/project/competitive-verifier/)

The library is inspired by [online-judge-tools/verification-helper](https://github.com/online-judge-tools/verification-helper).

- [Getting Started](https://competitive-verifier.github.io/competitive-verifier/installer.html) / [日本語](https://competitive-verifier.github.io/competitive-verifier/installer.ja.html)
- [Reference](https://competitive-verifier.github.io/competitive-verifier/document.html) / [日本語](https://competitive-verifier.github.io/competitive-verifier/document.ja.html)
- [DESIGN(日本語)](https://competitive-verifier.github.io/competitive-verifier/DESIGN)


## Get started

### Use in GitHub Actions

See [GitHub Pages](https://competitive-verifier.github.io/competitive-verifier/installer.html).
[日本語](https://competitive-verifier.github.io/competitive-verifier/installer.ja.html)

### Use in local

#### Install(local)

Needs Python 3.9 or greater.

```sh
pip install competitive-verifier
```

Or

```sh
pip install git+https://github.com/competitive-verifier/competitive-verifier.git@latest
```

**Migrate from verification-helper**

Run this script.

```sh
competitive-verifier migrate
```

## Development for contributors

```sh
pip install -U poetry
poetry install

# test
poetry run pytest

# format
poetry run poe format
```