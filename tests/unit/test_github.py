import os

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import github


@pytest.fixture
def workflow_ref(mocker: MockerFixture, request: pytest.FixtureRequest):
    mocker.patch.dict(
        os.environ,
        {"GITHUB_WORKFLOW_REF": request.param} if request.param else {},
        clear=True,
    )


@pytest.mark.usefixtures("workflow_ref")
@pytest.mark.parametrize(
    ("workflow_ref", "expected"),
    [
        (
            None,
            None,
        ),
        (
            "octocat/hello-world/.github/workflows/my-workflow.yml@refs/heads/my_branc",
            "my-workflow.yml",
        ),
    ],
    indirect=["workflow_ref"],
)
def test_workflow_filename(expected: str | None):
    assert github.env.get_workflow_filename() == expected
