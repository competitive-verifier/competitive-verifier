import filecmp
import inspect
import logging
import os
import pathlib
from dataclasses import dataclass
from itertools import chain
from typing import Any

import pytest
import yaml
from pytest_mock import MockerFixture
from pytest_subtests import SubTests

from competitive_verifier.documents.main import main
from competitive_verifier.oj import check_gnu_time

from .data.user_defined_and_python import UserDefinedAndPythonData
from .types import FilePaths


@dataclass
class MarkdownData:
    path: str
    front_matter: dict[str, Any]
    content: bytes = b""


@dataclass
class DocsData:
    root: pathlib.Path
    dest_root: pathlib.Path
    targets_data: list[MarkdownData]
    default_args: list[str]
    user_defined_and_python_data: UserDefinedAndPythonData


@pytest.fixture
def data(
    file_paths: FilePaths,
    user_defined_and_python_data: UserDefinedAndPythonData,
) -> DocsData:
    conf = user_defined_and_python_data.config_dir_path
    verify = conf / "verify.json"
    result = conf / "result.json"
    return DocsData(
        root=file_paths.root,
        dest_root=file_paths.dest_root,
        user_defined_and_python_data=user_defined_and_python_data,
        default_args=[
            "--verify-json",
            str(verify),
            str(result),
        ],
        targets_data=[
            MarkdownData(
                path="encoding/EUC-KR.txt.md",
                front_matter={
                    "data": {
                        "attributes": {},
                        "dependencies": [
                            {"files": [], "type": "Depends on"},
                            {"files": [], "type": "Required by"},
                            {"files": [], "type": "Verified with"},
                        ],
                        "dependsOn": [],
                        "embedded": [
                            {
                                "code": "컴퓨터 프로그램(영국 영어: computer programme, 미국 영어: computer program)은 컴퓨터에서 실행될 때 특정 작업(specific task)을 수행하는 일련의 명령어들의 모음(집합)이다.[1][2] 특정 문제를 해결하기 위해 처리 방법과 순서를 기술하여 컴퓨터에 입력되는 일련의 명령문 집합체이며 대부분의 프로그램은 실행 중(즉, 명령어를 '불러들일' 때)에 사용자의 입력에 반응하도록 구현된 일련의 명령어들로 구성되어 있다. 대부분의 프로그램들은 하드디스크 등의 매체에 바이너리 형식의 파일로 저장되어 있다가 사용자가 실행시키면 메모리로 적재되어 실행된다. 컴퓨터 소프트웨어와 비슷한 뜻을 가지고 있다. \"컴퓨터프로그램저작물\"은 저작권법상 저작물로서 보호된다. 동법에서 컴퓨터프로그램저작물이라 함은 특정한 결과를 얻기 위하여 컴퓨터 등 정보처리능력을 가진 장치 내에서 직접 또는 간접으로 사용되는 일련의 지시?· 명령으로 표현된 창작물을 말한다. (대한민국 저작권법 제2조 16호 및 제4조 제1항 9호)",
                                "name": "default",
                            },
                            {"code": f"cp949{os.linesep}", "name": "bundled"},
                        ],
                        "isFailed": False,
                        "isVerificationFile": False,
                        "path": "encoding/EUC-KR.txt",
                        "pathExtension": "txt",
                        "requiredBy": [],
                        "timestamp": "1970-05-06 18:01:32.540000-08:00",
                        "verificationStatus": "LIBRARY_NO_TESTS",
                        "verifiedWith": [],
                    },
                    "documentation_of": "encoding/EUC-KR.txt",
                    "layout": "document",
                    "title": "encoding/EUC-KR.txt",
                },
            ),
            MarkdownData(
                path="encoding/cp932.txt.md",
                front_matter={
                    "data": {
                        "attributes": {},
                        "dependencies": [
                            {"files": [], "type": "Depends on"},
                            {"files": [], "type": "Required by"},
                            {"files": [], "type": "Verified with"},
                        ],
                        "dependsOn": [],
                        "embedded": [
                            {
                                "code": "雨ニモマケズ\n風ニモマケズ\n雪ニモ夏ノ暑サニモマケヌ\n丈夫ナカラダヲモチ\n慾ハナク\n決シテ瞋ラズ\nイツモシヅカニワラッテヰル\n一日ニ玄米四合ト\n味噌ト少シノ野菜ヲタベ\nアラユルコトヲ\nジブンヲカンジョウニ入レズニ\nヨクミキキシワカリ\nソシテワスレズ\n野原ﾉ松ﾉ林ﾉ陰ﾉ\n小ｻﾅ萱ﾌﾞｷﾉ小屋ﾆヰﾃ\n東ﾆ病気ﾉｺﾄﾞﾓｱﾚﾊﾞ\n行ｯﾃ看病ｼﾃﾔﾘ\n西ﾆﾂｶﾚﾀ母ｱﾚﾊﾞ\n行ｯﾃｿﾉ稲ﾉ束ｦ負ﾋ\n南ﾆ死ﾆｻｳﾅ人ｱﾚﾊﾞ\n行ｯﾃｺﾊｶﾞﾗﾅｸﾃﾓｲヽﾄｲﾋ\n北ﾆｹﾝｸヮﾔｿｼｮｳｶﾞｱﾚﾊﾞ\nﾂﾏﾗﾅｲｶﾗﾔﾒﾛﾄｲﾋ\nﾋﾃﾞﾘﾉﾄｷﾊﾅﾐﾀﾞｦﾅｶﾞｼ\nｻﾑｻﾉﾅﾂﾊｵﾛｵﾛｱﾙｷ\nﾐﾝﾅﾆﾃﾞｸﾉﾎﾞーﾄﾖﾊﾞﾚ\nﾎﾒﾗﾚﾓｾｽﾞ\nｸﾆﾓｻﾚｽﾞ\nｻｳｲﾌﾓﾉﾆ\nﾜﾀｼﾊﾅﾘﾀｲ",
                                "name": "default",
                            },
                            {"code": f"cp932{os.linesep}", "name": "bundled"},
                        ],
                        "isFailed": False,
                        "isVerificationFile": False,
                        "path": "encoding/cp932.txt",
                        "pathExtension": "txt",
                        "requiredBy": [],
                        "timestamp": "1974-11-24 03:31:21.920000+05:00",
                        "verificationStatus": "LIBRARY_NO_TESTS",
                        "verifiedWith": [],
                    },
                    "documentation_of": "encoding/cp932.txt",
                    "layout": "document",
                    "title": "encoding/cp932.txt",
                },
            ),
            MarkdownData(
                path="python/failure.mle.py.md",
                front_matter={
                    "data": {
                        "attributes": {
                            "MLE": "100",
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "dependencies": [
                            {
                                "files": [
                                    {
                                        "filename": "lib_all_failure.py",
                                        "icon": "LIBRARY_ALL_WA",
                                        "path": "python/lib_all_failure.py",
                                        "title": "Lib All failure",
                                    },
                                    {
                                        "filename": "lib_some_failure.py",
                                        "title": "Units📏",
                                        "icon": "LIBRARY_SOME_WA",
                                        "path": "python/lib_some_failure.py",
                                    },
                                ],
                                "type": "Depends on",
                            },
                            {"files": [], "type": "Required by"},
                            {"files": [], "type": "Verified with"},
                        ],
                        "dependsOn": [
                            "python/lib_all_failure.py",
                            "python/lib_some_failure.py",
                        ],
                        "documentPath": "python/sub/failure.mle.md",
                        "embedded": [
                            {
                                "code": pathlib.Path("python/failure.mle.py").read_text(
                                    encoding="utf-8"
                                ),
                                "name": "default",
                            }
                        ],
                        "isFailed": True,
                        "isVerificationFile": True,
                        "path": "python/failure.mle.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "testcases": [
                            {
                                "name": "example_00",
                                "environment": "Python",
                                "status": "MLE",
                                "elapsed": 5.34,
                                "memory": 89.12,
                            },
                            {
                                "name": "example_01",
                                "environment": "Python",
                                "status": "MLE",
                                "elapsed": 9.79,
                                "memory": 78.31,
                            },
                            {
                                "name": "random_00",
                                "environment": "Python",
                                "status": "MLE",
                                "elapsed": 4.8,
                                "memory": 6.08,
                            },
                            {
                                "name": "random_01",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 4.09,
                                "memory": 15.08,
                            },
                            {
                                "name": "random_02",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 3.33,
                                "memory": 6.99,
                            },
                            {
                                "name": "random_03",
                                "environment": "Python",
                                "status": "MLE",
                                "elapsed": 4.04,
                                "memory": 9.04,
                            },
                            {
                                "name": "random_04",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 8.19,
                                "memory": 81.73,
                            },
                            {
                                "name": "random_05",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 0.18,
                                "memory": 47.13,
                            },
                            {
                                "name": "random_06",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 1.01,
                                "memory": 68.03,
                            },
                            {
                                "name": "random_07",
                                "environment": "Python",
                                "status": "MLE",
                                "elapsed": 3.76,
                                "memory": 40.93,
                            },
                            {
                                "name": "random_08",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 1.32,
                                "memory": 69.99,
                            },
                            {
                                "name": "random_09",
                                "environment": "Python",
                                "status": "MLE",
                                "elapsed": 0.12,
                                "memory": 19.27,
                            },
                        ]
                        if check_gnu_time()
                        else [],
                        "timestamp": "2063-11-24 03:09:17.740000+12:00",
                        "verificationStatus": "TEST_WRONG_ANSWER",
                        "verifiedWith": [],
                    },
                    "documentation_of": "python/failure.mle.py",
                    "layout": "document",
                    "title": "Failure-MLE",
                },
            ),
            MarkdownData(
                path="python/failure.re.py.md",
                front_matter={
                    "data": {
                        "attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "dependencies": [
                            {
                                "files": [
                                    {
                                        "filename": "lib_all_failure.py",
                                        "icon": "LIBRARY_ALL_WA",
                                        "path": "python/lib_all_failure.py",
                                        "title": "Lib All failure",
                                    }
                                ],
                                "type": "Depends on",
                            },
                            {"files": [], "type": "Required by"},
                            {"files": [], "type": "Verified with"},
                        ],
                        "dependsOn": ["python/lib_all_failure.py"],
                        "documentPath": "failure.re.md",
                        "embedded": [
                            {
                                "code": pathlib.Path("python/failure.re.py").read_text(
                                    encoding="utf-8"
                                ),
                                "name": "default",
                            }
                        ],
                        "isFailed": True,
                        "isVerificationFile": True,
                        "path": "python/failure.re.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "testcases": [
                            {
                                "name": "example_00",
                                "environment": "Python",
                                "status": "RE",
                                "elapsed": 3.47,
                                "memory": 55.14,
                            },
                            {
                                "name": "example_01",
                                "environment": "Python",
                                "status": "RE",
                                "elapsed": 4.8,
                                "memory": 82.74,
                            },
                            {
                                "name": "random_00",
                                "environment": "Python",
                                "status": "RE",
                                "elapsed": 4.62,
                                "memory": 53.04,
                            },
                            {
                                "name": "random_01",
                                "environment": "Python",
                                "status": "RE",
                                "elapsed": 5.6,
                                "memory": 84.32,
                            },
                            {
                                "name": "random_02",
                                "environment": "Python",
                                "status": "RE",
                                "elapsed": 9.28,
                                "memory": 18.09,
                            },
                            {
                                "name": "random_03",
                                "environment": "Python",
                                "status": "RE",
                                "elapsed": 6.41,
                                "memory": 13.18,
                            },
                            {
                                "name": "random_04",
                                "environment": "Python",
                                "status": "RE",
                                "elapsed": 7.17,
                                "memory": 63.97,
                            },
                            {
                                "name": "random_05",
                                "environment": "Python",
                                "status": "RE",
                                "elapsed": 7.59,
                                "memory": 75.35,
                            },
                            {
                                "name": "random_06",
                                "environment": "Python",
                                "status": "RE",
                                "elapsed": 4.79,
                                "memory": 50.9,
                            },
                            {
                                "name": "random_07",
                                "environment": "Python",
                                "status": "RE",
                                "elapsed": 2.83,
                                "memory": 25.32,
                            },
                            {
                                "name": "random_08",
                                "environment": "Python",
                                "status": "RE",
                                "elapsed": 1.71,
                                "memory": 53.67,
                            },
                            {
                                "name": "random_09",
                                "environment": "Python",
                                "status": "RE",
                                "elapsed": 4.52,
                                "memory": 85.17,
                            },
                        ],
                        "timestamp": "2025-09-24 11:55:03.150000+03:00",
                        "verificationStatus": "TEST_WRONG_ANSWER",
                        "verifiedWith": [],
                    },
                    "documentation_of": "python/failure.re.py",
                    "layout": "document",
                    "title": "Failure-RE",
                },
            ),
            MarkdownData(
                path="python/failure.tle.py.md",
                front_matter={
                    "data": {
                        "attributes": {
                            "PROBLEM": "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A",
                            "TLE": "0.1",
                            "links": [
                                "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A"
                            ],
                        },
                        "dependencies": [
                            {
                                "files": [
                                    {
                                        "filename": "lib_all_failure.py",
                                        "icon": "LIBRARY_ALL_WA",
                                        "path": "python/lib_all_failure.py",
                                        "title": "Lib All failure",
                                    }
                                ],
                                "type": "Depends on",
                            },
                            {"files": [], "type": "Required by"},
                            {"files": [], "type": "Verified with"},
                        ],
                        "dependsOn": ["python/lib_all_failure.py"],
                        "documentPath": "python/sub/failure.tle.md",
                        "embedded": [
                            {
                                "code": pathlib.Path("python/failure.tle.py").read_text(
                                    encoding="utf-8"
                                ),
                                "name": "default",
                            }
                        ],
                        "isFailed": True,
                        "isVerificationFile": True,
                        "path": "python/failure.tle.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "testcases": [
                            {
                                "environment": "Python",
                                "name": "judge_data",
                                "status": "TLE",
                                "elapsed": 6.75,
                                "memory": 8.22,
                            },
                        ],
                        "timestamp": "2006-12-18 06:30:34.720000+10:00",
                        "verificationStatus": "TEST_WRONG_ANSWER",
                        "verifiedWith": [],
                    },
                    "documentation_of": "python/failure.tle.py",
                    "layout": "document",
                    "title": "Failure-TLE",
                },
            ),
            MarkdownData(
                path="python/failure.wa.py.md",
                front_matter={
                    "data": {
                        "attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "dependencies": [
                            {
                                "files": [
                                    {
                                        "filename": "lib_all_failure.py",
                                        "icon": "LIBRARY_ALL_WA",
                                        "path": "python/lib_all_failure.py",
                                        "title": "Lib All failure",
                                    },
                                    {
                                        "filename": "lib_some_skip_some_wa.py",
                                        "icon": "LIBRARY_SOME_WA",
                                        "path": "python/lib_some_skip_some_wa.py",
                                    },
                                ],
                                "type": "Depends on",
                            },
                            {"files": [], "type": "Required by"},
                            {"files": [], "type": "Verified with"},
                        ],
                        "dependsOn": [
                            "python/lib_all_failure.py",
                            "python/lib_some_skip_some_wa.py",
                        ],
                        "documentPath": "failure.wa.md",
                        "embedded": [
                            {
                                "code": pathlib.Path("python/failure.wa.py").read_text(
                                    encoding="utf-8"
                                ),
                                "name": "default",
                            }
                        ],
                        "isFailed": True,
                        "isVerificationFile": True,
                        "path": "python/failure.wa.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "testcases": [
                            {
                                "name": "example_00",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 1.89,
                                "memory": 34.41,
                            },
                            {
                                "name": "example_01",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 2.17,
                                "memory": 10.24,
                            },
                            {
                                "name": "random_00",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 3.25,
                                "memory": 7.82,
                            },
                            {
                                "name": "random_01",
                                "environment": "Python",
                                "status": "WA",
                                "elapsed": 7.41,
                                "memory": 81.13,
                            },
                            {
                                "name": "random_02",
                                "environment": "Python",
                                "status": "WA",
                                "elapsed": 1.53,
                                "memory": 91.42,
                            },
                            {
                                "name": "random_03",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 4.6,
                                "memory": 13.13,
                            },
                            {
                                "name": "random_04",
                                "environment": "Python",
                                "status": "WA",
                                "elapsed": 5.09,
                                "memory": 38.65,
                            },
                            {
                                "name": "random_05",
                                "environment": "Python",
                                "status": "WA",
                                "elapsed": 6.34,
                                "memory": 73.13,
                            },
                            {
                                "name": "random_06",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 3.13,
                                "memory": 32.18,
                            },
                            {
                                "name": "random_07",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 8.88,
                                "memory": 10.07,
                            },
                            {
                                "name": "random_08",
                                "environment": "Python",
                                "status": "WA",
                                "elapsed": 1.66,
                                "memory": 88.91,
                            },
                            {
                                "name": "random_09",
                                "environment": "Python",
                                "status": "WA",
                                "elapsed": 9.41,
                                "memory": 34.78,
                            },
                        ],
                        "timestamp": "1987-12-04 11:42:47.800000-07:00",
                        "verificationStatus": "TEST_WRONG_ANSWER",
                        "verifiedWith": [],
                    },
                    "documentation_of": "python/failure.wa.py",
                    "layout": "document",
                    "title": "Failure-WA",
                },
            ),
            MarkdownData(
                path="python/lib_all_failure.py.md",
                content=b"# Lib All failure",
                front_matter={
                    "data": {
                        "attributes": {"links": []},
                        "dependencies": [
                            {"files": [], "type": "Depends on"},
                            {"files": [], "type": "Required by"},
                            {
                                "files": [
                                    {
                                        "filename": "failure.mle.py",
                                        "icon": "TEST_WRONG_ANSWER",
                                        "path": "python/failure.mle.py",
                                        "title": "Failure-MLE",
                                    },
                                    {
                                        "filename": "failure.re.py",
                                        "icon": "TEST_WRONG_ANSWER",
                                        "path": "python/failure.re.py",
                                        "title": "Failure-RE",
                                    },
                                    {
                                        "filename": "failure.tle.py",
                                        "icon": "TEST_WRONG_ANSWER",
                                        "path": "python/failure.tle.py",
                                        "title": "Failure-TLE",
                                    },
                                    {
                                        "filename": "failure.wa.py",
                                        "icon": "TEST_WRONG_ANSWER",
                                        "path": "python/failure.wa.py",
                                        "title": "Failure-WA",
                                    },
                                ],
                                "type": "Verified with",
                            },
                        ],
                        "dependsOn": [],
                        "documentPath": "python/docs_lib_all_failure.md",
                        "embedded": [
                            {
                                "code": pathlib.Path(
                                    "python/lib_all_failure.py"
                                ).read_text(encoding="utf-8"),
                                "name": "default",
                            }
                        ],
                        "isFailed": True,
                        "isVerificationFile": False,
                        "path": "python/lib_all_failure.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "timestamp": "1974-05-03 17:27:38.760000-11:00",
                        "verificationStatus": "LIBRARY_ALL_WA",
                        "verifiedWith": [
                            "python/failure.mle.py",
                            "python/failure.re.py",
                            "python/failure.tle.py",
                            "python/failure.wa.py",
                        ],
                    },
                    "documentation_of": "python/lib_all_failure.py",
                    "layout": "document",
                    "title": "Lib All failure",
                },
            ),
            MarkdownData(
                path="python/lib_all_success.py.md",
                content=b"# Lib All Success",
                front_matter={
                    "data": {
                        "attributes": {"links": []},
                        "dependencies": [
                            {"files": [], "type": "Depends on"},
                            {"files": [], "type": "Required by"},
                            {
                                "files": [
                                    {
                                        "filename": "success2.py",
                                        "icon": "TEST_ACCEPTED",
                                        "path": "python/success2.py",
                                        "title": "Success2",
                                    }
                                ],
                                "type": "Verified with",
                            },
                        ],
                        "dependsOn": [],
                        "documentPath": "python/docs_lib_all_success.md",
                        "embedded": [
                            {
                                "code": pathlib.Path(
                                    "python/lib_all_success.py"
                                ).read_text(encoding="utf-8"),
                                "name": "default",
                            }
                        ],
                        "isFailed": False,
                        "isVerificationFile": False,
                        "path": "python/lib_all_success.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "timestamp": "2059-10-27 14:16:37.850000-02:00",
                        "verificationStatus": "LIBRARY_ALL_AC",
                        "verifiedWith": ["python/success2.py"],
                    },
                    "documentation_of": "python/lib_all_success.py",
                    "layout": "document",
                    "title": "Lib All Success",
                },
            ),
            MarkdownData(
                path="python/lib_skip.py.md",
                content=b"# Skip",
                front_matter={
                    "data": {
                        "attributes": {"links": []},
                        "dependencies": [
                            {"files": [], "type": "Depends on"},
                            {"files": [], "type": "Required by"},
                            {
                                "files": [
                                    {
                                        "filename": "skip.py",
                                        "icon": "TEST_WAITING_JUDGE",
                                        "path": "python/skip.py",
                                    }
                                ],
                                "type": "Verified with",
                            },
                        ],
                        "dependsOn": [],
                        "documentPath": "python/docs_lib_skip.md",
                        "embedded": [
                            {
                                "code": pathlib.Path("python/lib_skip.py").read_text(
                                    encoding="utf-8"
                                ),
                                "name": "default",
                            }
                        ],
                        "isFailed": False,
                        "isVerificationFile": False,
                        "path": "python/lib_skip.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "timestamp": "1992-02-27 21:48:42.830000-04:00",
                        "verificationStatus": "LIBRARY_NO_TESTS",
                        "verifiedWith": ["python/skip.py"],
                    },
                    "documentation_of": "python/lib_skip.py",
                    "layout": "document",
                    "title": "Skip Library",
                },
            ),
            MarkdownData(
                path="python/lib_some_failure.py.md",
                front_matter={
                    "data": {
                        "attributes": {"TITLE": "Units📏", "links": []},
                        "dependencies": [
                            {"files": [], "type": "Depends on"},
                            {"files": [], "type": "Required by"},
                            {
                                "files": [
                                    {
                                        "filename": "failure.mle.py",
                                        "icon": "TEST_WRONG_ANSWER",
                                        "path": "python/failure.mle.py",
                                        "title": "Failure-MLE",
                                    },
                                    {
                                        "filename": "success1.py",
                                        "icon": "TEST_ACCEPTED",
                                        "path": "python/success1.py",
                                        "title": "Success1",
                                    },
                                ],
                                "type": "Verified with",
                            },
                        ],
                        "dependsOn": [],
                        "embedded": [
                            {
                                "code": pathlib.Path(
                                    "python/lib_some_failure.py"
                                ).read_text(encoding="utf-8"),
                                "name": "default",
                            }
                        ],
                        "isFailed": True,
                        "isVerificationFile": False,
                        "path": "python/lib_some_failure.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "timestamp": "1979-10-23 04:53:31.440000+07:00",
                        "verificationStatus": "LIBRARY_SOME_WA",
                        "verifiedWith": [
                            "python/failure.mle.py",
                            "python/success1.py",
                        ],
                    },
                    "documentation_of": "python/lib_some_failure.py",
                    "layout": "document",
                    "title": "Units📏",
                },
            ),
            MarkdownData(
                path="python/lib_some_skip.py.md",
                front_matter={
                    "data": {
                        "attributes": {"links": []},
                        "dependencies": [
                            {"files": [], "type": "Depends on"},
                            {"files": [], "type": "Required by"},
                            {
                                "files": [
                                    {
                                        "filename": "success1.py",
                                        "icon": "TEST_ACCEPTED",
                                        "path": "python/success1.py",
                                        "title": "Success1",
                                    }
                                ],
                                "type": "Verified with",
                            },
                        ],
                        "dependsOn": [],
                        "embedded": [
                            {
                                "code": pathlib.Path(
                                    "python/lib_some_skip.py"
                                ).read_text(encoding="utf-8"),
                                "name": "default",
                            }
                        ],
                        "isFailed": False,
                        "isVerificationFile": False,
                        "path": "python/lib_some_skip.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "timestamp": "2014-03-20 04:17:19.730000+11:00",
                        "verificationStatus": "LIBRARY_ALL_AC",
                        "verifiedWith": ["python/success1.py"],
                    },
                    "documentation_of": "python/lib_some_skip.py",
                    "layout": "document",
                    "title": "python/lib_some_skip.py",
                },
            ),
            MarkdownData(
                path="python/lib_some_skip_some_wa.py.md",
                front_matter={
                    "data": {
                        "attributes": {"links": []},
                        "dependencies": [
                            {"files": [], "type": "Depends on"},
                            {"files": [], "type": "Required by"},
                            {
                                "files": [
                                    {
                                        "filename": "failure.wa.py",
                                        "icon": "TEST_WRONG_ANSWER",
                                        "path": "python/failure.wa.py",
                                        "title": "Failure-WA",
                                    },
                                    {
                                        "filename": "skip.py",
                                        "icon": "TEST_WAITING_JUDGE",
                                        "path": "python/skip.py",
                                    },
                                    {
                                        "filename": "success2.py",
                                        "icon": "TEST_ACCEPTED",
                                        "path": "python/success2.py",
                                        "title": "Success2",
                                    },
                                ],
                                "type": "Verified with",
                            },
                        ],
                        "dependsOn": [],
                        "embedded": [
                            {
                                "code": pathlib.Path(
                                    "python/lib_some_skip_some_wa.py"
                                ).read_text(encoding="utf-8"),
                                "name": "default",
                            }
                        ],
                        "isFailed": True,
                        "isVerificationFile": False,
                        "path": "python/lib_some_skip_some_wa.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "timestamp": "2040-07-11 20:28:24.310000-06:00",
                        "verificationStatus": "LIBRARY_SOME_WA",
                        "verifiedWith": [
                            "python/failure.wa.py",
                            "python/skip.py",
                            "python/success2.py",
                        ],
                    },
                    "documentation_of": "python/lib_some_skip_some_wa.py",
                    "layout": "document",
                    "title": "python/lib_some_skip_some_wa.py",
                },
            ),
            MarkdownData(
                path="python/skip.py.md",
                front_matter={
                    "data": {
                        "attributes": {
                            "IGNORE": "",
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "dependencies": [
                            {
                                "files": [
                                    {
                                        "filename": "lib_skip.py",
                                        "icon": "LIBRARY_NO_TESTS",
                                        "path": "python/lib_skip.py",
                                        "title": "Skip Library",
                                    },
                                    {
                                        "filename": "lib_some_skip_some_wa.py",
                                        "icon": "LIBRARY_SOME_WA",
                                        "path": "python/lib_some_skip_some_wa.py",
                                    },
                                ],
                                "type": "Depends on",
                            },
                            {"files": [], "type": "Required by"},
                            {"files": [], "type": "Verified with"},
                        ],
                        "dependsOn": [
                            "python/lib_skip.py",
                            "python/lib_some_skip_some_wa.py",
                        ],
                        "embedded": [
                            {
                                "code": pathlib.Path("python/skip.py").read_text(
                                    encoding="utf-8"
                                ),
                                "name": "default",
                            }
                        ],
                        "isFailed": False,
                        "isVerificationFile": True,
                        "path": "python/skip.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "testcases": [],
                        "timestamp": "2027-02-03 19:13:12.050000-07:00",
                        "verificationStatus": "TEST_WAITING_JUDGE",
                        "verifiedWith": [],
                    },
                    "documentation_of": "python/skip.py",
                    "layout": "document",
                    "title": "python/skip.py",
                },
            ),
            MarkdownData(
                path="python/success1.py.md",
                front_matter={
                    "data": {
                        "attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "dependencies": [
                            {
                                "files": [
                                    {
                                        "filename": "lib_some_failure.py",
                                        "title": "Units📏",
                                        "icon": "LIBRARY_SOME_WA",
                                        "path": "python/lib_some_failure.py",
                                    },
                                    {
                                        "filename": "lib_some_skip.py",
                                        "icon": "LIBRARY_ALL_AC",
                                        "path": "python/lib_some_skip.py",
                                    },
                                ],
                                "type": "Depends on",
                            },
                            {"files": [], "type": "Required by"},
                            {"files": [], "type": "Verified with"},
                        ],
                        "dependsOn": [
                            "python/lib_some_failure.py",
                            "python/lib_some_skip.py",
                        ],
                        "documentPath": "python/docs_success1.md",
                        "embedded": [
                            {
                                "code": pathlib.Path("python/success1.py").read_text(
                                    encoding="utf-8"
                                ),
                                "name": "default",
                            }
                        ],
                        "isFailed": False,
                        "isVerificationFile": True,
                        "path": "python/success1.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "testcases": [
                            {
                                "name": "example_00",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 8.66,
                                "memory": 14.97,
                            },
                            {
                                "name": "example_01",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 3.4,
                                "memory": 82.48,
                            },
                            {
                                "name": "random_00",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 6.01,
                                "memory": 69.23,
                            },
                            {
                                "name": "random_01",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 8.47,
                                "memory": 16.15,
                            },
                            {
                                "name": "random_02",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 1.28,
                                "memory": 88.6,
                            },
                            {
                                "name": "random_03",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 5.69,
                                "memory": 85.15,
                            },
                            {
                                "name": "random_04",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 2.52,
                                "memory": 74.99,
                            },
                            {
                                "name": "random_05",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 2.0,
                                "memory": 4.66,
                            },
                            {
                                "name": "random_06",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 4.46,
                                "memory": 13.48,
                            },
                            {
                                "name": "random_07",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 7.96,
                                "memory": 6.91,
                            },
                            {
                                "name": "random_08",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 7.67,
                                "memory": 39.47,
                            },
                            {
                                "name": "random_09",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 0.16,
                                "memory": 36.45,
                            },
                        ],
                        "timestamp": "1972-12-09 20:42:07.860000-01:00",
                        "verificationStatus": "TEST_ACCEPTED",
                        "verifiedWith": [],
                    },
                    "documentation_of": "python/success1.py",
                    "layout": "document",
                    "title": "Success1",
                },
            ),
            MarkdownData(
                path="python/success2.py.md",
                front_matter={
                    "data": {
                        "attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "dependencies": [
                            {
                                "files": [
                                    {
                                        "filename": "lib_all_success.py",
                                        "icon": "LIBRARY_ALL_AC",
                                        "path": "python/lib_all_success.py",
                                        "title": "Lib All Success",
                                    },
                                    {
                                        "filename": "lib_some_skip_some_wa.py",
                                        "icon": "LIBRARY_SOME_WA",
                                        "path": "python/lib_some_skip_some_wa.py",
                                    },
                                ],
                                "type": "Depends on",
                            },
                            {"files": [], "type": "Required by"},
                            {"files": [], "type": "Verified with"},
                        ],
                        "dependsOn": [
                            "python/lib_all_success.py",
                            "python/lib_some_skip_some_wa.py",
                        ],
                        "documentPath": "python/docs_success2.md",
                        "embedded": [
                            {
                                "code": pathlib.Path("python/success2.py").read_text(
                                    encoding="utf-8"
                                ),
                                "name": "default",
                            }
                        ],
                        "isFailed": False,
                        "isVerificationFile": True,
                        "path": "python/success2.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "testcases": [
                            {
                                "name": "example_00",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 1.1,
                                "memory": 53.93,
                            },
                            {
                                "name": "example_01",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 5.48,
                                "memory": 50.39,
                            },
                            {
                                "name": "random_00",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 9.31,
                                "memory": 58.92,
                            },
                            {
                                "name": "random_01",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 4.3,
                                "memory": 35.83,
                            },
                            {
                                "name": "random_02",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 2.64,
                                "memory": 87.34,
                            },
                            {
                                "name": "random_03",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 2.73,
                                "memory": 54.56,
                            },
                            {
                                "name": "random_04",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 5.98,
                                "memory": 34.29,
                            },
                            {
                                "name": "random_05",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 3.52,
                                "memory": 91.97,
                            },
                            {
                                "name": "random_06",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 7.15,
                                "memory": 79.87,
                            },
                            {
                                "name": "random_07",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 6.63,
                                "memory": 11.11,
                            },
                            {
                                "name": "random_08",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 6.53,
                                "memory": 74.19,
                            },
                            {
                                "name": "random_09",
                                "environment": "Python",
                                "status": "AC",
                                "elapsed": 7.4,
                                "memory": 27.16,
                            },
                        ],
                        "timestamp": "1977-03-05 16:44:55.840000-03:00",
                        "verificationStatus": "TEST_ACCEPTED",
                        "verifiedWith": [],
                    },
                    "documentation_of": "python/success2.py",
                    "layout": "document",
                    "title": "Success2",
                },
            ),
            MarkdownData(
                path="python/sub/no_dependants.py.md",
                front_matter={
                    "data": {
                        "attributes": {"links": []},
                        "dependencies": [
                            {
                                "files": [],
                                "type": "Depends on",
                            },
                            {"files": [], "type": "Required by"},
                            {"files": [], "type": "Verified with"},
                        ],
                        "dependsOn": [],
                        "embedded": [
                            {
                                "code": pathlib.Path(
                                    "python/sub/no_dependants.py"
                                ).read_text(encoding="utf-8"),
                                "name": "default",
                            }
                        ],
                        "isFailed": False,
                        "isVerificationFile": False,
                        "path": "python/sub/no_dependants.py",
                        "pathExtension": "py",
                        "requiredBy": [],
                        "timestamp": "2050-11-28 04:31:04.040000-08:00",
                        "verificationStatus": "LIBRARY_NO_TESTS",
                        "verifiedWith": [],
                    },
                    "documentation_of": "python/sub/no_dependants.py",
                    "layout": "document",
                    "title": "python/sub/no_dependants.py",
                },
            ),
        ],
    )


@pytest.fixture
def package_dst(file_paths: FilePaths):
    return file_paths.dest_root / "documents"


@pytest.fixture
def setup_docs(mocker: MockerFixture):
    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REF_NAME": "TESTING_GIT_REF",
            "GITHUB_WORKFLOW": "TESTING_WORKFLOW",
        },
    )


def check_common(
    destination: pathlib.Path,
    *,
    data: DocsData,
    subtests: SubTests,
):
    assert destination.is_dir()

    targets = {t.path: t for t in data.targets_data}

    for target_file in filter(
        lambda p: p.is_file(),
        chain.from_iterable(
            (
                (destination / "encoding").glob("**/*"),
                (destination / "python").glob("**/*"),
            )
        ),
    ):
        path_str = target_file.relative_to(destination).as_posix()
        with subtests.test(  # pyright: ignore[reportUnknownMemberType]
            msg="Check testdata", path=path_str
        ):
            target_value = target_file.read_bytes().strip()
            assert target_value.startswith(b"---\n")

            front_matter_end = target_value.index(b"---", 4)
            front_matter = yaml.safe_load(target_value[4:front_matter_end])
            content = target_value[front_matter_end + 3 :].strip()

            assert content == targets[path_str].content
            assert front_matter == targets[path_str].front_matter
        del targets[path_str]

    assert not list(targets.keys())


@pytest.mark.usefixtures("additional_path")
@pytest.mark.order(-100)
class TestCommandDocuments:
    @pytest.mark.integration
    @pytest.mark.usefixtures("setup_docs")
    def test_with_config(
        self,
        package_dst: pathlib.Path,
        data: DocsData,
        subtests: SubTests,
    ):
        destination = package_dst / inspect.stack()[0].function
        docs_settings_dir = data.root / "docs_settings"

        main(
            [
                "--docs",
                docs_settings_dir.as_posix(),
                "--destination",
                destination.as_posix(),
            ]
            + data.default_args
        )

        check_common(destination, data=data, subtests=subtests)

        config_yml = yaml.safe_load((destination / "_config.yml").read_bytes())
        assert config_yml == {
            "action_name": "TESTING_WORKFLOW",
            "basedir": "integration_test_data/UserDefinedAndPythonData/",
            "branch_name": "TESTING_GIT_REF",
            "description": "My description",
            "filename-index": True,
            "highlightjs-style": "vs2015",
            "plugins": [
                "jemoji",
                "jekyll-redirect-from",
                "jekyll-remote-theme",
            ],
            "mathjax": 2,
            "sass": {"style": "compressed"},
            "theme": "jekyll-theme-modernist",
            "icons": {
                "LIBRARY_ALL_AC": ":heavy_check_mark:",
                "LIBRARY_ALL_WA": ":x:",
                "LIBRARY_NO_TESTS": ":warning:",
                "LIBRARY_PARTIAL_AC": ":heavy_check_mark:",
                "LIBRARY_SOME_WA": ":question:",
                "TEST_ACCEPTED": ":100:",
                "TEST_WAITING_JUDGE": ":warning:",
                "TEST_WRONG_ANSWER": ":x:",
            },
        }

        assert (destination / "static.md").exists()
        assert (destination / "static.md").read_text(
            encoding="utf-8"
        ) == "# Static page\n\nI'm Static!"

        static_dir = docs_settings_dir / "static"
        for static_file in filter(lambda p: p.is_file(), static_dir.glob("**/*")):
            assert filecmp.cmp(
                static_file, destination / static_file.relative_to(static_dir)
            )

    @pytest.mark.integration
    @pytest.mark.usefixtures("setup_docs")
    def test_without_config(
        self,
        package_dst: pathlib.Path,
        data: DocsData,
        subtests: SubTests,
    ):
        destination = package_dst / inspect.stack()[0].function

        main(
            [
                "--docs",
                "testdata/nothing",
                "--destination",
                destination.as_posix(),
            ]
            + data.default_args
        )

        check_common(destination, data=data, subtests=subtests)

        config_yml = yaml.safe_load((destination / "_config.yml").read_bytes())
        assert config_yml == {
            "action_name": "TESTING_WORKFLOW",
            "basedir": "integration_test_data/UserDefinedAndPythonData/",
            "branch_name": "TESTING_GIT_REF",
            "description": '<small>This documentation is automatically generated by <a href="https://github.com/competitive-verifier/competitive-verifier">competitive-verifier/competitive-verifier</a></small>',
            "filename-index": False,
            "highlightjs-style": "default",
            "plugins": [
                "jemoji",
                "jekyll-redirect-from",
                "jekyll-remote-theme",
            ],
            "mathjax": 3,
            "sass": {"style": "compressed"},
            "theme": "jekyll-theme-minimal",
            "icons": {
                "LIBRARY_ALL_AC": ":heavy_check_mark:",
                "LIBRARY_ALL_WA": ":x:",
                "LIBRARY_NO_TESTS": ":warning:",
                "LIBRARY_PARTIAL_AC": ":heavy_check_mark:",
                "LIBRARY_SOME_WA": ":question:",
                "TEST_ACCEPTED": ":heavy_check_mark:",
                "TEST_WAITING_JUDGE": ":warning:",
                "TEST_WRONG_ANSWER": ":x:",
            },
        }

        assert not (destination / "static.md").exists()

        resource_dir = pathlib.Path("src/competitive_verifier_resources/jekyll")
        for resource_file in filter(lambda p: p.is_file(), resource_dir.glob("**/*")):
            assert filecmp.cmp(
                resource_file, destination / resource_file.relative_to(resource_dir)
            )

    @pytest.mark.integration
    @pytest.mark.usefixtures("setup_docs")
    def test_logging_default(
        self,
        package_dst: pathlib.Path,
        data: DocsData,
        subtests: SubTests,
        caplog: pytest.LogCaptureFixture,
    ):
        caplog.set_level(logging.WARNING)
        destination = package_dst / inspect.stack()[0].function

        main(
            [
                "--docs",
                "testdata/nothing",
                "--destination",
                destination.as_posix(),
            ]
            + data.default_args
        )

        check_common(destination, data=data, subtests=subtests)

        assert caplog.record_tuples == [
            (
                "competitive_verifier.documents.job",
                logging.WARNING,
                "the `documentation_of` path of dummy/dummy.md is not target: ./dummy.py",
            )
        ]

    @pytest.mark.integration
    @pytest.mark.usefixtures("setup_docs")
    def test_logging_include(
        self,
        package_dst: pathlib.Path,
        data: DocsData,
        subtests: SubTests,
        caplog: pytest.LogCaptureFixture,
    ):
        caplog.set_level(logging.WARNING)
        destination = package_dst / inspect.stack()[0].function

        main(
            [
                "--include",
                "python/",
                "encoding",
                "failure.*.md",
                "--docs",
                "testdata/nothing",
                "--destination",
                destination.as_posix(),
            ]
            + data.default_args
        )

        check_common(destination, data=data, subtests=subtests)

        assert not caplog.record_tuples

    @pytest.mark.parametrize(
        "exclude",
        [
            ["dummy/"],
            ["dummy/dummy.md"],
        ],
    )
    @pytest.mark.integration
    @pytest.mark.usefixtures("setup_docs")
    def test_logging_exclude(
        self,
        exclude: list[str],
        package_dst: pathlib.Path,
        data: DocsData,
        subtests: SubTests,
        caplog: pytest.LogCaptureFixture,
    ):
        caplog.set_level(logging.WARNING)
        destination = package_dst / inspect.stack()[0].function

        main(
            [
                "--exclude",
                *exclude,
                "--docs",
                "testdata/nothing",
                "--destination",
                destination.as_posix(),
            ]
            + data.default_args
        )

        check_common(destination, data=data, subtests=subtests)

        assert not caplog.record_tuples
