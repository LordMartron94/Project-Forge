# Created by LordMartron on 18/08/2025.

import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Optional

from project_forge.common.py_common.logging import HoornLogger
from project_forge.constants import SCRIPTS_DIR


# noinspection t
def commit_with_ps(
        logger: HoornLogger,
        repo_path: Path,
        message: str,
        add: Iterable[str] = (".",),
        *,
        only_if_changes: bool = True,
        amend: bool = False,
        signoff: bool = False,
        no_verify: bool = False,
        push: bool = False,
        remote: str = "origin",
        branch: str = "",
        gpg_sign: bool = False,
        timeout_sec: int = 120,
        log_separator: str = "APP.Commit",
) -> bool:
    """
    Wraps scripts/commit_changes.ps1
    Returns True if commit (or push) ran successfully; False if skipped (no changes).
    Raises on hard errors (missing PS, script not found, PS failure).
    """
    script: Path = SCRIPTS_DIR.joinpath("git_commit_changes.ps1").resolve()
    if not script.exists():
        raise FileNotFoundError(f"commit script not found: {script}")

    ps_exe: Optional[str] = shutil.which("powershell.exe") or shutil.which("pwsh")
    if not ps_exe:
        raise RuntimeError("PowerShell not found on PATH.")

    cmd = [
        ps_exe,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-File", str(script),
        "-RepoPath", str(repo_path),
        "-Message", f'"{message}"',
    ]

    # -Add can be specified multiple times
    for a in add:
        cmd += ["-Add", a]

    if only_if_changes: cmd.append("-OnlyIfChanges")
    if amend:           cmd.append("-Amend")
    if signoff:         cmd.append("-Signoff")
    if no_verify:       cmd.append("-NoVerify")
    if push:            cmd.append("-Push")
    if gpg_sign:        cmd.append("-GpgSign")
    if remote:          cmd += ["-Remote", remote]
    if branch:          cmd += ["-Branch", branch]

    logger.debug(f"Committing via PS: {message}", separator=log_separator)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)

    if result.stderr:
        for line in result.stderr.splitlines():
            if not line.strip():
                continue
            lower = line.lower()
            if "warning:" in lower:
                logger.warning(line, separator=log_separator)
            elif "error:" in lower:
                logger.error(line, separator=log_separator)
            else:
                logger.info(line, separator=log_separator)

    if result.returncode == 0:
        # Heuristic: the script prints “No changes to commit. Skipping.” to STDOUT when skipping.
        skipped = "No changes to commit" in (result.stdout or "")
        return not skipped
    else:
        raise RuntimeError(f"Commit script failed (exit {result.returncode}).")
