from typing import NamedTuple


class NotLoggedInError(RuntimeError):
    pass


class TestCase(NamedTuple):
    name: str
    input_name: str
    input_data: bytes
    output_name: str
    output_data: bytes
