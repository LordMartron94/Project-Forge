# Created by LordMartron on 18/08/2025.

import shutil
import subprocess
from pathlib import Path
from typing import Optional, Sequence

from project_forge.common.py_common.logging import HoornLogger
from project_forge.constants import SCRIPTS_DIR
from project_forge.git_commit_helper import commit_with_ps


# noinspection t
def enforce_eol_policy(
        logger: HoornLogger,
        repo_path: Path,
        *,
        commit: bool = False,
        commit_message: str = "Project Forge: Normalize line endings per .gitattributes",
        timeout_sec: int = 180,
        log_separator: str = "APP.Normalize",
) -> bool:
    """
    Execute scripts/configure_git_repo.ps1 to:
      - Align repo-local Git EOL config inferred from .gitattributes (e.g., core.eol/autocrlf)
      - Run: git add --renormalize .   (inside the script)

    Optionally commit any staged normalization changes.

    Returns True iff a commit was created (when commit=True); False otherwise.
    Raises RuntimeError on script error.

    NOTE: This replaces the previous behavior that called correctly_configure_git_repo.ps1.
          The function name is preserved to avoid breaking callers.
    """
    script = SCRIPTS_DIR.joinpath("configure_git_repo.ps1").resolve()
    if not script.exists():
        raise FileNotFoundError(f"Normalization script not found: {script}")

    # Prefer pwsh if available; fall back to Windows PowerShell
    ps_exe: Optional[str] = shutil.which("pwsh") or shutil.which("powershell") or shutil.which("powershell.exe")
    if not ps_exe:
        raise RuntimeError("PowerShell not found on PATH.")

    cmd: Sequence[str] = [
        ps_exe,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-File", str(script),
        "-RepoPath", str(repo_path),
    ]

    logger.debug("Configuring from .gitattributes and renormalizing…", separator=log_separator)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)

    if result.stdout:
        logger.info(result.stdout.strip(), separator=log_separator)
    if result.stderr:
        # The script prints clean errors to stdout; stderr may contain benign git warnings.
        if result.returncode == 0:
            logger.warning(result.stderr.strip(), separator=log_separator)
        else:
            logger.error(result.stderr.strip(), separator=log_separator)

    if result.returncode != 0:
        raise RuntimeError(f"Renormalization script failed (exit {result.returncode}).")

    if not commit:
        return False

    # Commit any staged renormalized files (idempotent if none).
    committed = commit_with_ps(
        logger=logger,
        repo_path=repo_path,
        message=commit_message,
        add=["."],              # script already staged changes; add-all is safe & idempotent
        only_if_changes=True,
    )

    return committed
