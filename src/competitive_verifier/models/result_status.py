from enum import Enum


class ResultStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"

    @property
    def status(self) -> "ResultStatus":
        return self


class JudgeStatus(Enum):
    AC = "AC"
    WA = "WA"
    RE = "RE"
    TLE = "TLE"
    MLE = "MLE"
