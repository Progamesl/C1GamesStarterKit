#!/usr/bin/env python3
"""Build the self-contained, flattened Milestone 9 submission package."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V6_DIR = ROOT / "baselines" / "defense_v6_encryptor_fix"
DENSE_SOURCE = ROOT / "baselines" / "defense_v15_dense_opening" / "algo_strategy.py"
PACKAGE_ROOT = ROOT / "submissions" / "milestone9_champion"
OUTPUT_NAME = "defense_v15_dense_opening_flat_algo_folder"
OUTPUT_DIR = PACKAGE_ROOT / OUTPUT_NAME
ARCHIVE = PACKAGE_ROOT / "defense_v15_dense_opening_flat_permfix.zip"

V6_ENTRYPOINT = '''if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
'''


def render_flat_strategy() -> str:
    v6_source = (V6_DIR / "algo_strategy.py").read_text(encoding="utf-8")
    dense_source = DENSE_SOURCE.read_text(encoding="utf-8")

    if v6_source.count("class AlgoStrategy(gamelib.AlgoCore):") != 1:
        raise RuntimeError("unexpected v6 class declaration")
    if v6_source.count(V6_ENTRYPOINT) != 1:
        raise RuntimeError("unexpected v6 entrypoint")

    v6_source = v6_source.replace(
        "class AlgoStrategy(gamelib.AlgoCore):",
        "class V6AlgoStrategy(gamelib.AlgoCore):",
        1,
    ).replace(V6_ENTRYPOINT, "", 1)

    dense_start = dense_source.index("class AlgoStrategy(v6.AlgoStrategy):")
    dense_end = dense_source.index('\n\nif __name__ == "__main__":', dense_start)
    dense_class = dense_source[dense_start:dense_end]
    dense_class = dense_class.replace(
        "class AlgoStrategy(v6.AlgoStrategy):",
        "class AlgoStrategy(V6AlgoStrategy):",
        1,
    ).replace("v6.", "")

    return (
        "# Flattened Milestone 9 champion: full accepted v6 strategy and dense\n"
        "# opening specialization in one top-level source file. This package has\n"
        "# no dynamic imports or repository-relative strategy dependencies.\n\n"
        + v6_source.rstrip()
        + "\n\n\n"
        + dense_class.rstrip()
        + '\n\n\nif __name__ == "__main__":\n'
        + "    AlgoStrategy().start()\n"
    )


def copy_runtime_files() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    (OUTPUT_DIR / "algo_strategy.py").write_text(
        render_flat_strategy(), encoding="utf-8"
    )
    shutil.copy2(V6_DIR / "algo.json", OUTPUT_DIR / "algo.json")
    shutil.copy2(V6_DIR / "run.sh", OUTPUT_DIR / "run.sh")
    os.chmod(OUTPUT_DIR / "run.sh", 0o755)
    shutil.copytree(
        V6_DIR / "gamelib",
        OUTPUT_DIR / "gamelib",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )


def write_archive() -> None:
    if ARCHIVE.exists():
        ARCHIVE.unlink()
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUTPUT_DIR.rglob("*")):
            relative = Path(OUTPUT_NAME) / path.relative_to(OUTPUT_DIR)
            name = relative.as_posix() + ("/" if path.is_dir() else "")
            info = zipfile.ZipInfo(name, date_time=(2026, 7, 16, 0, 0, 0))
            info.create_system = 3
            if path.is_dir():
                info.external_attr = (stat.S_IFDIR | 0o755) << 16
                archive.writestr(info, b"")
            else:
                # Explicitly retain Unix permission bits, especially run.sh.
                mode = stat.S_IMODE(path.stat().st_mode)
                info.external_attr = (stat.S_IFREG | mode) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())


def main() -> None:
    copy_runtime_files()
    write_archive()
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    print(f"folder={OUTPUT_DIR}")
    print(f"archive={ARCHIVE}")
    print(f"sha256={digest}")


if __name__ == "__main__":
    main()
