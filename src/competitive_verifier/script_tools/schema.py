import json

from pydantic import BaseModel

import competitive_verifier.models


def dump_json_schema(cls: type[BaseModel]):
    return json.dumps(
        cls.model_json_schema(),
        indent=2,
    )


def show_verify_json_schema():
    print(dump_json_schema(competitive_verifier.models.VerificationInput))


def show_result_json_schema():
    print(dump_json_schema(competitive_verifier.models.VerifyCommandResult))
