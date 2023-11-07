import filecmp
import inspect
import logging
import os
import pathlib
from typing import Any

import pytest
import yaml
from pydantic import BaseModel
from pytest_mock import MockerFixture
from pytest_subtests import SubTests

from competitive_verifier.documents.main import main
from competitive_verifier.oj import check_gnu_time

from .data.user_defined_and_python import UserDefinedAndPythonData
from .types import FilePaths


class MarkdownData(BaseModel):
    path: str
    front_matter: dict[str, Any]
    content: bytes = b""


class DocsData(FilePaths):
    targets_data: list[MarkdownData]
    default_args: list[str]


@pytest.fixture
def data(
    file_paths: FilePaths,
    user_defined_and_python_data: UserDefinedAndPythonData,
) -> DocsData:
    conf = user_defined_and_python_data.conf_path
    verify = conf / "verify.json"
    result = conf / "result.json"
    return DocsData.model_validate(
        file_paths.model_dump()
        | {
            "default_args": [
                "--verify-json",
                str(verify),
                str(result),
            ],
            "targets_data": [
                MarkdownData(
                    path=f"{file_paths.targets}/encoding/EUC-KR.txt.md",
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
                            "path": f"{file_paths.targets}/encoding/EUC-KR.txt",
                            "pathExtension": "txt",
                            "requiredBy": [],
                            "timestamp": "2043-02-15 18:11:02.510000-11:00",
                            "verificationStatus": "LIBRARY_NO_TESTS",
                            "verifiedWith": [],
                        },
                        "documentation_of": f"{file_paths.targets}/encoding/EUC-KR.txt",
                        "layout": "document",
                        "title": f"{file_paths.targets}/encoding/EUC-KR.txt",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/encoding/cp932.txt.md",
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
                            "path": f"{file_paths.targets}/encoding/cp932.txt",
                            "pathExtension": "txt",
                            "requiredBy": [],
                            "timestamp": "2053-04-11 19:18:33.220000+10:00",
                            "verificationStatus": "LIBRARY_NO_TESTS",
                            "verifiedWith": [],
                        },
                        "documentation_of": f"{file_paths.targets}/encoding/cp932.txt",
                        "layout": "document",
                        "title": f"{file_paths.targets}/encoding/cp932.txt",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/failure.mle.py.md",
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
                                            "path": f"{file_paths.targets}/python/lib_all_failure.py",
                                            "title": "Lib All failure",
                                        },
                                        {
                                            "filename": "lib_some_failure.py",
                                            "title": "Units📏",
                                            "icon": "LIBRARY_SOME_WA",
                                            "path": f"{file_paths.targets}/python/lib_some_failure.py",
                                        },
                                    ],
                                    "type": "Depends on",
                                },
                                {"files": [], "type": "Required by"},
                                {"files": [], "type": "Verified with"},
                            ],
                            "dependsOn": [
                                f"{file_paths.targets}/python/lib_all_failure.py",
                                f"{file_paths.targets}/python/lib_some_failure.py",
                            ],
                            "documentPath": f"{file_paths.targets}/python/sub/failure.mle.md",
                            "embedded": [
                                {
                                    "code": pathlib.Path(
                                        f"{file_paths.targets}/python/failure.mle.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": True,
                            "isVerificationFile": True,
                            "path": f"{file_paths.targets}/python/failure.mle.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "testcases": [
                                {
                                    "elapsed": 6.26,
                                    "environment": "Python",
                                    "memory": 60.26,
                                    "name": "example_00",
                                    "status": "MLE",
                                },
                                {
                                    "elapsed": 2.4,
                                    "environment": "Python",
                                    "memory": 59.44,
                                    "name": "example_01",
                                    "status": "MLE",
                                },
                                {
                                    "elapsed": 6.48,
                                    "environment": "Python",
                                    "memory": 7.31,
                                    "name": "random_00",
                                    "status": "MLE",
                                },
                                {
                                    "elapsed": 9.73,
                                    "environment": "Python",
                                    "memory": 24.23,
                                    "name": "random_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.88,
                                    "environment": "Python",
                                    "memory": 52.64,
                                    "name": "random_02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.47,
                                    "environment": "Python",
                                    "memory": 29.96,
                                    "name": "random_03",
                                    "status": "MLE",
                                },
                                {
                                    "elapsed": 7.88,
                                    "environment": "Python",
                                    "memory": 34.93,
                                    "name": "random_04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.89,
                                    "environment": "Python",
                                    "memory": 71.35,
                                    "name": "random_05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.13,
                                    "environment": "Python",
                                    "memory": 38.93,
                                    "name": "random_06",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.77,
                                    "environment": "Python",
                                    "memory": 84.25,
                                    "name": "random_07",
                                    "status": "MLE",
                                },
                                {
                                    "elapsed": 4.06,
                                    "environment": "Python",
                                    "memory": 42.35,
                                    "name": "random_08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.99,
                                    "environment": "Python",
                                    "memory": 10.53,
                                    "name": "random_09",
                                    "status": "MLE",
                                },
                            ]
                            if check_gnu_time()
                            else [],
                            "timestamp": "1995-01-16 12:45:06.250000-12:00",
                            "verificationStatus": "TEST_WRONG_ANSWER",
                            "verifiedWith": [],
                        },
                        "documentation_of": f"{file_paths.targets}/python/failure.mle.py",
                        "layout": "document",
                        "title": "Failure-MLE",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/failure.re.py.md",
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
                                            "path": f"{file_paths.targets}/python/lib_all_failure.py",
                                            "title": "Lib All failure",
                                        }
                                    ],
                                    "type": "Depends on",
                                },
                                {"files": [], "type": "Required by"},
                                {"files": [], "type": "Verified with"},
                            ],
                            "dependsOn": [
                                f"{file_paths.targets}/python/lib_all_failure.py"
                            ],
                            "documentPath": f"{file_paths.targets}/failure.re.md",
                            "embedded": [
                                {
                                    "code": pathlib.Path(
                                        f"{file_paths.targets}/python/failure.re.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": True,
                            "isVerificationFile": True,
                            "path": f"{file_paths.targets}/python/failure.re.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "testcases": [
                                {
                                    "elapsed": 9.89,
                                    "environment": "Python",
                                    "memory": 58.09,
                                    "name": "example_00",
                                    "status": "RE",
                                },
                                {
                                    "elapsed": 1.1,
                                    "environment": "Python",
                                    "memory": 96.01,
                                    "name": "example_01",
                                    "status": "RE",
                                },
                                {
                                    "elapsed": 2.24,
                                    "environment": "Python",
                                    "memory": 41.05,
                                    "name": "random_00",
                                    "status": "RE",
                                },
                                {
                                    "elapsed": 9.27,
                                    "environment": "Python",
                                    "memory": 38.67,
                                    "name": "random_01",
                                    "status": "RE",
                                },
                                {
                                    "elapsed": 1.62,
                                    "environment": "Python",
                                    "memory": 28.54,
                                    "name": "random_02",
                                    "status": "RE",
                                },
                                {
                                    "elapsed": 1.36,
                                    "environment": "Python",
                                    "memory": 51.34,
                                    "name": "random_03",
                                    "status": "RE",
                                },
                                {
                                    "elapsed": 2.44,
                                    "environment": "Python",
                                    "memory": 26.1,
                                    "name": "random_04",
                                    "status": "RE",
                                },
                                {
                                    "elapsed": 2.89,
                                    "environment": "Python",
                                    "memory": 26.67,
                                    "name": "random_05",
                                    "status": "RE",
                                },
                                {
                                    "elapsed": 8.76,
                                    "environment": "Python",
                                    "memory": 41.03,
                                    "name": "random_06",
                                    "status": "RE",
                                },
                                {
                                    "elapsed": 0.86,
                                    "environment": "Python",
                                    "memory": 29.6,
                                    "name": "random_07",
                                    "status": "RE",
                                },
                                {
                                    "elapsed": 1.56,
                                    "environment": "Python",
                                    "memory": 46.89,
                                    "name": "random_08",
                                    "status": "RE",
                                },
                                {
                                    "elapsed": 0.32,
                                    "environment": "Python",
                                    "memory": 94.85,
                                    "name": "random_09",
                                    "status": "RE",
                                },
                            ],
                            "timestamp": "2051-10-31 15:18:39.670000+05:00",
                            "verificationStatus": "TEST_WRONG_ANSWER",
                            "verifiedWith": [],
                        },
                        "documentation_of": f"{file_paths.targets}/python/failure.re.py",
                        "layout": "document",
                        "title": "Failure-RE",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/failure.tle.py.md",
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
                                            "path": f"{file_paths.targets}/python/lib_all_failure.py",
                                            "title": "Lib All failure",
                                        }
                                    ],
                                    "type": "Depends on",
                                },
                                {"files": [], "type": "Required by"},
                                {"files": [], "type": "Verified with"},
                            ],
                            "dependsOn": [
                                f"{file_paths.targets}/python/lib_all_failure.py"
                            ],
                            "documentPath": f"{file_paths.targets}/python/sub/failure.tle.md",
                            "embedded": [
                                {
                                    "code": pathlib.Path(
                                        f"{file_paths.targets}/python/failure.tle.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": True,
                            "isVerificationFile": True,
                            "path": f"{file_paths.targets}/python/failure.tle.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "testcases": [
                                {
                                    "environment": "Python",
                                    "name": "judge_data",
                                    "status": "TLE",
                                    "elapsed": 5.76,
                                    "memory": 20.14,
                                },
                            ],
                            "timestamp": "1984-11-13 14:12:14.730000+11:00",
                            "verificationStatus": "TEST_WRONG_ANSWER",
                            "verifiedWith": [],
                        },
                        "documentation_of": f"{file_paths.targets}/python/failure.tle.py",
                        "layout": "document",
                        "title": "Failure-TLE",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/failure.wa.py.md",
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
                                            "path": f"{file_paths.targets}/python/lib_all_failure.py",
                                            "title": "Lib All failure",
                                        },
                                        {
                                            "filename": "lib_some_skip_some_wa.py",
                                            "icon": "LIBRARY_SOME_WA",
                                            "path": f"{file_paths.targets}/python/lib_some_skip_some_wa.py",
                                        },
                                    ],
                                    "type": "Depends on",
                                },
                                {"files": [], "type": "Required by"},
                                {"files": [], "type": "Verified with"},
                            ],
                            "dependsOn": [
                                f"{file_paths.targets}/python/lib_all_failure.py",
                                f"{file_paths.targets}/python/lib_some_skip_some_wa.py",
                            ],
                            "documentPath": f"{file_paths.targets}/failure.wa.md",
                            "embedded": [
                                {
                                    "code": pathlib.Path(
                                        f"{file_paths.targets}/python/failure.wa.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": True,
                            "isVerificationFile": True,
                            "path": f"{file_paths.targets}/python/failure.wa.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "testcases": [
                                {
                                    "elapsed": 8.82,
                                    "environment": "Python",
                                    "memory": 90.49,
                                    "name": "example_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.18,
                                    "environment": "Python",
                                    "memory": 77.99,
                                    "name": "example_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.75,
                                    "environment": "Python",
                                    "memory": 27.37,
                                    "name": "random_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.06,
                                    "environment": "Python",
                                    "memory": 86.57,
                                    "name": "random_01",
                                    "status": "WA",
                                },
                                {
                                    "elapsed": 9.79,
                                    "environment": "Python",
                                    "memory": 4.53,
                                    "name": "random_02",
                                    "status": "WA",
                                },
                                {
                                    "elapsed": 4.02,
                                    "environment": "Python",
                                    "memory": 71.02,
                                    "name": "random_03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.75,
                                    "environment": "Python",
                                    "memory": 55.4,
                                    "name": "random_04",
                                    "status": "WA",
                                },
                                {
                                    "elapsed": 3.46,
                                    "environment": "Python",
                                    "memory": 7.43,
                                    "name": "random_05",
                                    "status": "WA",
                                },
                                {
                                    "elapsed": 5.18,
                                    "environment": "Python",
                                    "memory": 8.11,
                                    "name": "random_06",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.66,
                                    "environment": "Python",
                                    "memory": 31.86,
                                    "name": "random_07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.82,
                                    "environment": "Python",
                                    "memory": 5.56,
                                    "name": "random_08",
                                    "status": "WA",
                                },
                                {
                                    "elapsed": 7.69,
                                    "environment": "Python",
                                    "memory": 38.28,
                                    "name": "random_09",
                                    "status": "WA",
                                },
                            ],
                            "timestamp": "2032-11-02 18:46:36.440000+07:00",
                            "verificationStatus": "TEST_WRONG_ANSWER",
                            "verifiedWith": [],
                        },
                        "documentation_of": f"{file_paths.targets}/python/failure.wa.py",
                        "layout": "document",
                        "title": "Failure-WA",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/lib_all_failure.py.md",
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
                                            "path": f"{file_paths.targets}/python/failure.mle.py",
                                            "title": "Failure-MLE",
                                        },
                                        {
                                            "filename": "failure.re.py",
                                            "icon": "TEST_WRONG_ANSWER",
                                            "path": f"{file_paths.targets}/python/failure.re.py",
                                            "title": "Failure-RE",
                                        },
                                        {
                                            "filename": "failure.tle.py",
                                            "icon": "TEST_WRONG_ANSWER",
                                            "path": f"{file_paths.targets}/python/failure.tle.py",
                                            "title": "Failure-TLE",
                                        },
                                        {
                                            "filename": "failure.wa.py",
                                            "icon": "TEST_WRONG_ANSWER",
                                            "path": f"{file_paths.targets}/python/failure.wa.py",
                                            "title": "Failure-WA",
                                        },
                                    ],
                                    "type": "Verified with",
                                },
                            ],
                            "dependsOn": [],
                            "documentPath": f"{file_paths.targets}/python/docs_lib_all_failure.md",
                            "embedded": [
                                {
                                    "code": pathlib.Path(
                                        f"{file_paths.targets}/python/lib_all_failure.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": True,
                            "isVerificationFile": False,
                            "path": f"{file_paths.targets}/python/lib_all_failure.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "timestamp": "2010-03-22 15:25:58.780000-09:00",
                            "verificationStatus": "LIBRARY_ALL_WA",
                            "verifiedWith": [
                                f"{file_paths.targets}/python/failure.mle.py",
                                f"{file_paths.targets}/python/failure.re.py",
                                f"{file_paths.targets}/python/failure.tle.py",
                                f"{file_paths.targets}/python/failure.wa.py",
                            ],
                        },
                        "documentation_of": f"{file_paths.targets}/python/lib_all_failure.py",
                        "layout": "document",
                        "title": "Lib All failure",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/lib_all_success.py.md",
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
                                            "path": f"{file_paths.targets}/python/success2.py",
                                            "title": "Success2",
                                        }
                                    ],
                                    "type": "Verified with",
                                },
                            ],
                            "dependsOn": [],
                            "documentPath": f"{file_paths.targets}/python/docs_lib_all_success.md",
                            "embedded": [
                                {
                                    "code": pathlib.Path(
                                        f"{file_paths.targets}/python/lib_all_success.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": False,
                            "isVerificationFile": False,
                            "path": f"{file_paths.targets}/python/lib_all_success.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "timestamp": "2038-10-10 06:55:28.880000+01:00",
                            "verificationStatus": "LIBRARY_ALL_AC",
                            "verifiedWith": [
                                f"{file_paths.targets}/python/success2.py"
                            ],
                        },
                        "documentation_of": f"{file_paths.targets}/python/lib_all_success.py",
                        "layout": "document",
                        "title": "Lib All Success",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/lib_skip.py.md",
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
                                            "path": f"{file_paths.targets}/python/skip.py",
                                        }
                                    ],
                                    "type": "Verified with",
                                },
                            ],
                            "dependsOn": [],
                            "documentPath": f"{file_paths.targets}/python/docs_lib_skip.md",
                            "embedded": [
                                {
                                    "code": pathlib.Path(
                                        f"{file_paths.targets}/python/lib_skip.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": False,
                            "isVerificationFile": False,
                            "path": f"{file_paths.targets}/python/lib_skip.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "timestamp": "2052-01-29 15:38:28.410000+04:00",
                            "verificationStatus": "LIBRARY_NO_TESTS",
                            "verifiedWith": [f"{file_paths.targets}/python/skip.py"],
                        },
                        "documentation_of": f"{file_paths.targets}/python/lib_skip.py",
                        "layout": "document",
                        "title": "Skip Library",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/lib_some_failure.py.md",
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
                                            "path": f"{file_paths.targets}/python/failure.mle.py",
                                            "title": "Failure-MLE",
                                        },
                                        {
                                            "filename": "success1.py",
                                            "icon": "TEST_ACCEPTED",
                                            "path": f"{file_paths.targets}/python/success1.py",
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
                                        f"{file_paths.targets}/python/lib_some_failure.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": True,
                            "isVerificationFile": False,
                            "path": f"{file_paths.targets}/python/lib_some_failure.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "timestamp": "1995-05-25 04:00:57.780000-09:00",
                            "verificationStatus": "LIBRARY_SOME_WA",
                            "verifiedWith": [
                                f"{file_paths.targets}/python/failure.mle.py",
                                f"{file_paths.targets}/python/success1.py",
                            ],
                        },
                        "documentation_of": f"{file_paths.targets}/python/lib_some_failure.py",
                        "layout": "document",
                        "title": "Units📏",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/lib_some_skip.py.md",
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
                                            "path": f"{file_paths.targets}/python/success1.py",
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
                                        f"{file_paths.targets}/python/lib_some_skip.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": False,
                            "isVerificationFile": False,
                            "path": f"{file_paths.targets}/python/lib_some_skip.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "timestamp": "2011-01-03 02:51:38.890000+02:00",
                            "verificationStatus": "LIBRARY_ALL_AC",
                            "verifiedWith": [
                                f"{file_paths.targets}/python/success1.py"
                            ],
                        },
                        "documentation_of": f"{file_paths.targets}/python/lib_some_skip.py",
                        "layout": "document",
                        "title": f"{file_paths.targets}/python/lib_some_skip.py",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/lib_some_skip_some_wa.py.md",
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
                                            "path": f"{file_paths.targets}/python/failure.wa.py",
                                            "title": "Failure-WA",
                                        },
                                        {
                                            "filename": "skip.py",
                                            "icon": "TEST_WAITING_JUDGE",
                                            "path": f"{file_paths.targets}/python/skip.py",
                                        },
                                        {
                                            "filename": "success2.py",
                                            "icon": "TEST_ACCEPTED",
                                            "path": f"{file_paths.targets}/python/success2.py",
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
                                        f"{file_paths.targets}/python/lib_some_skip_some_wa.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": True,
                            "isVerificationFile": False,
                            "path": f"{file_paths.targets}/python/lib_some_skip_some_wa.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "timestamp": "2028-02-07 01:58:01.410000+04:00",
                            "verificationStatus": "LIBRARY_SOME_WA",
                            "verifiedWith": [
                                f"{file_paths.targets}/python/failure.wa.py",
                                f"{file_paths.targets}/python/skip.py",
                                f"{file_paths.targets}/python/success2.py",
                            ],
                        },
                        "documentation_of": f"{file_paths.targets}/python/lib_some_skip_some_wa.py",
                        "layout": "document",
                        "title": f"{file_paths.targets}/python/lib_some_skip_some_wa.py",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/skip.py.md",
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
                                            "path": f"{file_paths.targets}/python/lib_skip.py",
                                            "title": "Skip Library",
                                        },
                                        {
                                            "filename": "lib_some_skip_some_wa.py",
                                            "icon": "LIBRARY_SOME_WA",
                                            "path": f"{file_paths.targets}/python/lib_some_skip_some_wa.py",
                                        },
                                    ],
                                    "type": "Depends on",
                                },
                                {"files": [], "type": "Required by"},
                                {"files": [], "type": "Verified with"},
                            ],
                            "dependsOn": [
                                f"{file_paths.targets}/python/lib_skip.py",
                                f"{file_paths.targets}/python/lib_some_skip_some_wa.py",
                            ],
                            "embedded": [
                                {
                                    "code": pathlib.Path(
                                        f"{file_paths.targets}/python/skip.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": False,
                            "isVerificationFile": True,
                            "path": f"{file_paths.targets}/python/skip.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "testcases": [],
                            "timestamp": "2055-01-20 20:33:06.930000+06:00",
                            "verificationStatus": "TEST_WAITING_JUDGE",
                            "verifiedWith": [],
                        },
                        "documentation_of": f"{file_paths.targets}/python/skip.py",
                        "layout": "document",
                        "title": f"{file_paths.targets}/python/skip.py",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/success1.py.md",
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
                                            "path": f"{file_paths.targets}/python/lib_some_failure.py",
                                        },
                                        {
                                            "filename": "lib_some_skip.py",
                                            "icon": "LIBRARY_ALL_AC",
                                            "path": f"{file_paths.targets}/python/lib_some_skip.py",
                                        },
                                    ],
                                    "type": "Depends on",
                                },
                                {"files": [], "type": "Required by"},
                                {"files": [], "type": "Verified with"},
                            ],
                            "dependsOn": [
                                f"{file_paths.targets}/python/lib_some_failure.py",
                                f"{file_paths.targets}/python/lib_some_skip.py",
                            ],
                            "documentPath": f"{file_paths.targets}/python/docs_success1.md",
                            "embedded": [
                                {
                                    "code": pathlib.Path(
                                        f"{file_paths.targets}/python/success1.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": False,
                            "isVerificationFile": True,
                            "path": f"{file_paths.targets}/python/success1.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "testcases": [
                                {
                                    "elapsed": 1.43,
                                    "environment": "Python",
                                    "memory": 64.25,
                                    "name": "example_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.2,
                                    "environment": "Python",
                                    "memory": 70.28,
                                    "name": "example_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.39,
                                    "environment": "Python",
                                    "memory": 86.29,
                                    "name": "random_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.65,
                                    "environment": "Python",
                                    "memory": 90.22,
                                    "name": "random_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.69,
                                    "environment": "Python",
                                    "memory": 5.04,
                                    "name": "random_02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.85,
                                    "environment": "Python",
                                    "memory": 9.68,
                                    "name": "random_03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.36,
                                    "environment": "Python",
                                    "memory": 72.4,
                                    "name": "random_04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.56,
                                    "environment": "Python",
                                    "memory": 66.47,
                                    "name": "random_05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.28,
                                    "environment": "Python",
                                    "memory": 36.75,
                                    "name": "random_06",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 6.04,
                                    "environment": "Python",
                                    "memory": 47.31,
                                    "name": "random_07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.93,
                                    "environment": "Python",
                                    "memory": 35.68,
                                    "name": "random_08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.7,
                                    "environment": "Python",
                                    "memory": 21.75,
                                    "name": "random_09",
                                    "status": "AC",
                                },
                            ],
                            "timestamp": "2016-09-12 09:18:45.880000+01:00",
                            "verificationStatus": "TEST_ACCEPTED",
                            "verifiedWith": [],
                        },
                        "documentation_of": f"{file_paths.targets}/python/success1.py",
                        "layout": "document",
                        "title": "Success1",
                    },
                ),
                MarkdownData(
                    path=f"{file_paths.targets}/python/success2.py.md",
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
                                            "path": f"{file_paths.targets}/python/lib_all_success.py",
                                            "title": "Lib All Success",
                                        },
                                        {
                                            "filename": "lib_some_skip_some_wa.py",
                                            "icon": "LIBRARY_SOME_WA",
                                            "path": f"{file_paths.targets}/python/lib_some_skip_some_wa.py",
                                        },
                                    ],
                                    "type": "Depends on",
                                },
                                {"files": [], "type": "Required by"},
                                {"files": [], "type": "Verified with"},
                            ],
                            "dependsOn": [
                                f"{file_paths.targets}/python/lib_all_success.py",
                                f"{file_paths.targets}/python/lib_some_skip_some_wa.py",
                            ],
                            "documentPath": f"{file_paths.targets}/python/docs_success2.md",
                            "embedded": [
                                {
                                    "code": pathlib.Path(
                                        f"{file_paths.targets}/python/success2.py"
                                    ).read_text(encoding="utf-8"),
                                    "name": "default",
                                }
                            ],
                            "isFailed": False,
                            "isVerificationFile": True,
                            "path": f"{file_paths.targets}/python/success2.py",
                            "pathExtension": "py",
                            "requiredBy": [],
                            "testcases": [
                                {
                                    "elapsed": 6.73,
                                    "environment": "Python",
                                    "memory": 11.63,
                                    "name": "example_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.64,
                                    "environment": "Python",
                                    "memory": 89.38,
                                    "name": "example_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 6.05,
                                    "environment": "Python",
                                    "memory": 66.15,
                                    "name": "random_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.86,
                                    "environment": "Python",
                                    "memory": 41.39,
                                    "name": "random_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.8,
                                    "environment": "Python",
                                    "memory": 62.2,
                                    "name": "random_02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.92,
                                    "environment": "Python",
                                    "memory": 99.71,
                                    "name": "random_03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.85,
                                    "environment": "Python",
                                    "memory": 71.44,
                                    "name": "random_04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.4,
                                    "environment": "Python",
                                    "memory": 92.24,
                                    "name": "random_05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.64,
                                    "environment": "Python",
                                    "memory": 21.41,
                                    "name": "random_06",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.51,
                                    "environment": "Python",
                                    "memory": 24.87,
                                    "name": "random_07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.97,
                                    "environment": "Python",
                                    "memory": 49.86,
                                    "name": "random_08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.74,
                                    "environment": "Python",
                                    "memory": 77.54,
                                    "name": "random_09",
                                    "status": "AC",
                                },
                            ],
                            "timestamp": "1984-04-02 07:11:46.490000+12:00",
                            "verificationStatus": "TEST_ACCEPTED",
                            "verifiedWith": [],
                        },
                        "documentation_of": f"{file_paths.targets}/python/success2.py",
                        "layout": "document",
                        "title": "Success2",
                    },
                ),
            ],
        }
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
        (destination / data.targets).glob("**/*"),
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
            "basedir": "integration_test_data/",
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
            "basedir": "integration_test_data/",
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
                data.targets,
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
