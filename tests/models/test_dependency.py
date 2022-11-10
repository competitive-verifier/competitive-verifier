from pathlib import Path

from competitive_verifier.models import (
    ConstVerification,
    DependencyResolver,
    VerificationFile,
    VerificationInput,
)

test_input = VerificationInput(
    files={
        Path("foo/bar1.py"): VerificationFile(dependencies=[]),
        Path("foo/bar2.py"): VerificationFile(
            dependencies=[Path("foo/bar1.py")],
        ),
        Path("foo/baz.py"): VerificationFile(dependencies=[]),
        Path("foo/barbaz.py"): VerificationFile(
            dependencies=[
                Path("foo/bar2.py"),
                Path("foo/baz.py"),
            ],
        ),
        Path("hoge/1.py"): VerificationFile(
            dependencies=[],
        ),
        Path("hoge/hoge.py"): VerificationFile(
            dependencies=[
                Path("hoge/fuga.py"),
                Path("hoge/1.py"),
            ],
        ),
        Path("hoge/piyo.py"): VerificationFile(
            dependencies=[
                Path("hoge/fuga.py"),
                Path("hoge/hoge.py"),
            ],
        ),
        Path("hoge/fuga.py"): VerificationFile(
            dependencies=[
                Path("hoge/piyo.py"),
            ],
        ),
        Path("hoge/piyopiyo.py"): VerificationFile(
            dependencies=[
                Path("hoge/piyo.py"),
            ],
        ),
        Path("test/test.py"): VerificationFile(
            verification=[ConstVerification(status="success")],  # type:ignore
            dependencies=[
                Path("hoge/piyopiyo.py"),
            ],
        ),
    }
)


def test_depends_on():
    simple = {
        "foo/bar1.py": [],
        "foo/bar2.py": [("foo/bar1.py")],
        "foo/baz.py": [],
        "foo/barbaz.py": ["foo/bar2.py", "foo/baz.py"],
        "hoge/1.py": [],
        "hoge/piyo.py": ["hoge/fuga.py"],
        "hoge/fuga.py": ["hoge/piyo.py"],
        "hoge/piyopiyo.py": ["hoge/piyo.py"],
        "test/test.py": ["hoge/piyopiyo.py"],
    }
    expected = {Path(p): set(Path(s) for s in d) for p, d in simple.items()}

    resolver = DependencyResolver(test_input, excluded_files={Path("hoge/hoge.py")})
    assert resolver.depends_on == expected


def test_required_by():
    simple = {
        "foo/bar1.py": ["foo/bar2.py"],
        "foo/bar2.py": ["foo/barbaz.py"],
        "foo/baz.py": ["foo/barbaz.py"],
        "foo/barbaz.py": [],
        "hoge/1.py": [],
        "hoge/piyo.py": ["hoge/fuga.py", "hoge/piyopiyo.py"],
        "hoge/fuga.py": ["hoge/piyo.py"],
        "hoge/piyopiyo.py": [],
        "test/test.py": [],
    }
    expected = {Path(p): set(Path(s) for s in d) for p, d in simple.items()}

    resolver = DependencyResolver(test_input, excluded_files={Path("hoge/hoge.py")})
    assert resolver.required_by == expected


def test_verified_with():
    simple = {
        "foo/bar1.py": [],
        "foo/bar2.py": [],
        "foo/baz.py": [],
        "foo/barbaz.py": [],
        "hoge/1.py": [],
        "hoge/piyo.py": [],
        "hoge/fuga.py": [],
        "hoge/piyopiyo.py": ["test/test.py"],
        "test/test.py": [],
    }
    expected = {Path(p): set(Path(s) for s in d) for p, d in simple.items()}

    resolver = DependencyResolver(test_input, excluded_files={Path("hoge/hoge.py")})
    assert resolver.verified_with == expected


def test_verified_with2():
    simple: dict[str, list[str]] = {
        "foo/bar1.py": [],
        "foo/bar2.py": [],
        "foo/baz.py": [],
        "foo/barbaz.py": [],
        "hoge/1.py": [],
        "hoge/hoge.py": [],
        "hoge/piyo.py": [],
        "hoge/fuga.py": [],
        "hoge/piyopiyo.py": [],
    }
    expected = {Path(p): set(Path(s) for s in d) for p, d in simple.items()}

    resolver = DependencyResolver(test_input, excluded_files={Path("test/test.py")})
    assert resolver.verified_with == expected
