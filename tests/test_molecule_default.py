from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def test_molecule_default_scenario() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    molecule = shutil.which("molecule")

    assert molecule is not None, "molecule is not installed or not on PATH"

    result = subprocess.run(
        [molecule, "test", "-s", "default"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        "molecule default scenario failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
