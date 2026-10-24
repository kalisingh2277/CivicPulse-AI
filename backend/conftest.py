# Ensures `app` is importable in tests without installing the project.
import pytest

import app.api.v1.complaints as complaints_api


@pytest.fixture(autouse=True, scope="session")
def _deterministic_pipeline() -> None:
    # Don't auto-run the AI pipeline on complaint create during tests — AI tests call
    # run_pipeline() explicitly so behaviour is deterministic, and console/complaint
    # tests can rely on freshly-created complaints staying in the triage queue.
    async def _noop(complaint_id: str) -> None:
        return None

    complaints_api.run_pipeline = _noop
    complaints_api.run_analyze_media = _noop
