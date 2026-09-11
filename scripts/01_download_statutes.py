"""
Clones civictech-India/Indian-Law-Penal-Code-Json into a temp dir and copies
cpc.json into data/statutes/.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_URL = "https://github.com/civictech-India/Indian-Law-Penal-Code-Json"
REPO_ROOT = Path(__file__).resolve().parents[1]
STATUTES_DIR = REPO_ROOT / "data" / "statutes"


def main() -> None:
    STATUTES_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        clone_dir = Path(tmp) / "indian-law-json"
        print(f"Cloning {REPO_URL} ...")
        subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, str(clone_dir)],
            check=True,
        )

        src = clone_dir / "cpc.json"
        if not src.exists():
            matches = list(clone_dir.rglob("cpc.json"))
            if not matches:
                print(f"cpc.json not found anywhere in {clone_dir}", file=sys.stderr)
                sys.exit(1)
            src = matches[0]

        dst = STATUTES_DIR / "cpc.json"
        shutil.copy(src, dst)
        print(f"Copied {src} -> {dst}")


if __name__ == "__main__":
    main()
