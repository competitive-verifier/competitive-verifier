import datetime
import enum
import pathlib

from pydantic import BaseModel

from competitive_verifier import git

from .file import VerificationFile, VerificationInput
from .result import ResultStatus, VerifyCommandResult


class VerificationStatus(str, enum.Enum):
    icon: str
    is_success: bool

    @property
    def is_failed(self) -> bool:
        return not self.is_success

    def __new__(
        cls, title: str, icon: str = "", is_success: bool = False
    ) -> "VerificationStatus":

        obj = str.__new__(cls, title)
        obj._value_ = title

        obj.icon = icon
        obj.is_success = is_success
        return obj

    LIBRARY_ALL_AC = ("LIBRARY_ALL_AC", ":heavy_check_mark:", True)
    LIBRARY_PARTIAL_AC = ("LIBRARY_PARTIAL_AC", ":question:", True)
    LIBRARY_SOME_WA = ("LIBRARY_SOME_WA", ":question:", False)
    LIBRARY_ALL_WA = ("LIBRARY_ALL_WA", ":x:", False)
    LIBRARY_NO_TESTS = ("LIBRARY_NO_TESTS", ":warning:", True)
    TEST_ACCEPTED = ("TEST_ACCEPTED", ":heavy_check_mark:", True)
    TEST_WRONG_ANSWER = ("TEST_WRONG_ANSWER", ":x:", False)
    TEST_WAITING_JUDGE = ("TEST_WAITING_JUDGE", ":warning:", True)


class _VerificationStatusFlag(enum.Flag):
    TEST_NOTHING = 0
    IS_LIBRARY = enum.auto()
    HAVE_AC = enum.auto()
    HAVE_WA = enum.auto()
    HAVE_SKIP = enum.auto()

    LIBRARY_AC_WA_SKIP = IS_LIBRARY | HAVE_AC | HAVE_WA | HAVE_SKIP
    LIBRARY_AC_WA = IS_LIBRARY | HAVE_AC | HAVE_WA
    LIBRARY_AC_SKIP = IS_LIBRARY | HAVE_AC | HAVE_SKIP
    LIBRARY_AC = IS_LIBRARY | HAVE_AC
    LIBRARY_WA_SKIP = IS_LIBRARY | HAVE_WA | HAVE_SKIP
    LIBRARY_WA = IS_LIBRARY | HAVE_WA
    LIBRARY_SKIP = IS_LIBRARY | HAVE_SKIP
    LIBRARY_NOTHING = IS_LIBRARY

    TEST_AC_WA_SKIP = HAVE_AC | HAVE_WA | HAVE_SKIP
    TEST_AC_WA = HAVE_AC | HAVE_WA
    TEST_AC_SKIP = HAVE_AC | HAVE_SKIP
    TEST_AC = HAVE_AC
    TEST_WA_SKIP = HAVE_WA | HAVE_SKIP
    TEST_WA = HAVE_WA
    TEST_SKIP = HAVE_SKIP

    @classmethod
    @property
    def _conv_dict(cls) -> dict["_VerificationStatusFlag", VerificationStatus]:
        try:
            d: dict["_VerificationStatusFlag", VerificationStatus] = cls._conv_dict_attr  # type: ignore
        except AttributeError:
            d = {
                cls.LIBRARY_AC_WA_SKIP: VerificationStatus.LIBRARY_SOME_WA,
                cls.LIBRARY_AC_WA: VerificationStatus.LIBRARY_SOME_WA,
                cls.LIBRARY_AC_SKIP: VerificationStatus.LIBRARY_PARTIAL_AC,
                cls.LIBRARY_AC: VerificationStatus.LIBRARY_ALL_AC,
                cls.LIBRARY_WA_SKIP: VerificationStatus.LIBRARY_ALL_WA,
                cls.LIBRARY_WA: VerificationStatus.LIBRARY_ALL_WA,
                cls.LIBRARY_SKIP: VerificationStatus.LIBRARY_NO_TESTS,
                cls.LIBRARY_NOTHING: VerificationStatus.LIBRARY_NO_TESTS,
                cls.TEST_AC_WA_SKIP: VerificationStatus.TEST_WRONG_ANSWER,
                cls.TEST_AC_WA: VerificationStatus.TEST_WRONG_ANSWER,
                cls.TEST_AC_SKIP: VerificationStatus.TEST_WAITING_JUDGE,
                cls.TEST_AC: VerificationStatus.TEST_ACCEPTED,
                cls.TEST_WA_SKIP: VerificationStatus.TEST_WRONG_ANSWER,
                cls.TEST_WA: VerificationStatus.TEST_WRONG_ANSWER,
                cls.TEST_SKIP: VerificationStatus.TEST_WAITING_JUDGE,
                cls.TEST_NOTHING: VerificationStatus.TEST_WAITING_JUDGE,
            }
        return d

    def to_status(self) -> VerificationStatus:
        return self._conv_dict[self]


class SourceCodeStat(BaseModel):
    path: pathlib.Path
    file_input: VerificationFile
    is_verification: bool
    verification_status: VerificationStatus
    timestamp: datetime.datetime
    depends_on: set[pathlib.Path]
    required_by: set[pathlib.Path]
    verified_with: set[pathlib.Path]


def filter_edge(
    edges: dict[pathlib.Path, set[pathlib.Path]],
    excluded: set[pathlib.Path],
) -> dict[pathlib.Path, set[pathlib.Path]]:
    d: dict[pathlib.Path, set[pathlib.Path]] = {}
    for p, s in edges.items():
        if p not in excluded:
            d[p] = s - excluded
    return d


def resolve_dependency(
    *,
    input: VerificationInput,
    result: VerifyCommandResult,
    included_files: set[pathlib.Path],
) -> dict[pathlib.Path, SourceCodeStat]:
    d: dict[pathlib.Path, SourceCodeStat] = {}
    statuses: dict[pathlib.Path, _VerificationStatusFlag] = {
        p: _VerificationStatusFlag.TEST_NOTHING for p in input.files.keys()
    }

    for p, r in result.files.items():
        if p not in included_files:
            continue
        st = _VerificationStatusFlag.TEST_NOTHING
        for v in r.verifications:
            if v.status == ResultStatus.SUCCESS:
                st |= _VerificationStatusFlag.HAVE_AC
            elif v.status == ResultStatus.FAILURE:
                st |= _VerificationStatusFlag.HAVE_WA
            elif v.status == ResultStatus.SKIPPED:
                st |= _VerificationStatusFlag.HAVE_SKIP
        statuses[p] = st

    for group in input.scc():
        group &= included_files
        if not group:
            continue

        group_status = _VerificationStatusFlag.TEST_NOTHING

        for path in group:
            assert path in statuses
            group_status |= statuses[path]

        for path in group:
            depends_on = input.depends_on[path] & included_files
            required_by = input.required_by[path] & included_files
            verified_with = input.verified_with[path] & included_files

            for dep in depends_on:
                statuses[dep] |= group_status

            timestamp = git.get_commit_time(input.transitive_depends_on[path])
            file_input = input.files[path]
            is_verification = file_input.is_verification()

            flag_status = group_status
            if not is_verification:
                flag_status |= _VerificationStatusFlag.IS_LIBRARY

            d[path] = SourceCodeStat(
                path=path,
                file_input=file_input,
                is_verification=is_verification,
                depends_on=depends_on,
                required_by=required_by,
                verified_with=verified_with,
                timestamp=timestamp,
                verification_status=flag_status.to_status(),
            )
    return d
