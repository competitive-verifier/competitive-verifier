import logging

from competitive_verifier.log import GitHubMessageParams
from tests import LogComparer


def test_comparer():
    assert LogComparer(message="123") == LogComparer(message="123")
    assert LogComparer(message="123") != LogComparer(message="124")

    assert LogComparer(message="123") == logging.makeLogRecord(
        {"msg": "%d", "args": (123,)}
    )
    assert LogComparer(message="123") != logging.makeLogRecord(
        {"msg": "%d", "args": (124,)}
    )

    assert LogComparer(message="123", level=1) == logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "levelno": 1}
    )
    assert LogComparer(message="123", level=1) != logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "levelno": 2}
    )

    assert LogComparer(message="123", name="1") == logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "name": "1"}
    )
    assert LogComparer(message="123", name="1") != logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "name": "2"}
    )

    assert LogComparer(
        message="123", github=GitHubMessageParams(title="air")
    ) == logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "github": GitHubMessageParams(title="air")}
    )
    assert LogComparer(
        message="123", github=GitHubMessageParams(title="air2")
    ) != logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "github": GitHubMessageParams(title="air")}
    )
    assert LogComparer(message="123") != logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "github": GitHubMessageParams(title="air")}
    )
