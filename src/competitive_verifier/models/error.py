class VerifierError(Exception):
    def __init__(
        self,
        message: str,
        *,
        inner: BaseException | None = None,
    ) -> None:
        self.message = message
        self.inner = inner
