import re

from . import models

_ESHRAM_PATTERN = re.compile(r"^[A-Za-z0-9]{8,20}$")


def run_mock_eshram_check(worker: models.WorkerProfile) -> tuple[bool, str]:
    """Stand-in for a real e-Shram/NSDC lookup - there's no live API wired
    up yet, so this just checks the ID's shape. Swap this function's body
    for a real API call later; callers only depend on the (verified, note)
    shape, not on how the check is done."""
    eshram_id = (worker.eshram_id or "").strip()
    if not eshram_id:
        return False, "No e-Shram/NSDC ID on file."
    if not _ESHRAM_PATTERN.match(eshram_id):
        return False, "e-Shram/NSDC ID doesn't match the expected format."
    return True, f"e-Shram/NSDC ID {eshram_id} validated (mock check)."
