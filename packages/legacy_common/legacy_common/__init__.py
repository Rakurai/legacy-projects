"""legacy_common – shared modules for legacy MUD analysis tools."""

from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[3]
ARTIFACTS_DIR: Path = REPO_ROOT / "artifacts"
