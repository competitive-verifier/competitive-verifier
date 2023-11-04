import pathlib
import sys
from hashlib import md5

from competitive_verifier.models import (
    FileResult,
    TestcaseResult,
    VerificationResult,
    VerifyCommandResult,
)


def md5_number(seed: bytes):
    return int(md5(seed).hexdigest(), 16)


def rewriteTestcaseResult(seed: bytes, case: TestcaseResult):
    seed += (case.name or "").encode()
    seed += case.status.name.encode()

    case.elapsed = md5_number(seed + b"elapsed") % 1000 / 100
    case.memory = md5_number(seed + b"memory") % 10000 / 100
    return case


def rewriteVerificationResult(seed: bytes, verification: VerificationResult):
    seed += (verification.verification_name or "").encode()
    seed += verification.status.name.encode()

    verification.elapsed = md5_number(seed + b"elapsed") % 10000

    if verification.slowest:
        verification.slowest = verification.elapsed // 10
    if verification.heaviest:
        verification.heaviest = md5_number(seed + b"heaviest") % 1000

    if verification.testcases:
        verification.testcases = [
            rewriteTestcaseResult(seed, c) for c in verification.testcases
        ]

    return verification


def rewriteFileResult(path: pathlib.Path, file_result: FileResult):
    seed = path.as_posix().encode()
    file_result.verifications = [
        rewriteVerificationResult(seed, v) for v in file_result.verifications
    ]
    return file_result


def rewriteVerifyCommandResult(result: VerifyCommandResult):
    result.total_seconds = 1234
    result.files = {k: rewriteFileResult(k, v) for k, v in result.files.items()}
    return result


def main(result_path: pathlib.Path):
    result = VerifyCommandResult.model_validate_json(result_path.read_bytes())
    json = rewriteVerifyCommandResult(result).model_dump_json(exclude_none=True)
    # print(json)
    result_path.write_text(json)


if __name__ == "__main__":
    main(pathlib.Path(sys.argv[1]))
