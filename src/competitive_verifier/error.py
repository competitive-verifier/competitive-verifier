from typing import Optional


class VerifierError(Exception):
    def __init__(
        self,
        message: str,
        *,
        inner: Optional[BaseException] = None,
    ) -> None:
        self.message = message
        self.inner = inner
