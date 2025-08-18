import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from project_forge.common.py_common.logging import HoornLogger
from project_forge.common.py_common.patterns import IPipe
from project_forge.common.py_common.user_input.user_input_helper import UserInputHelper
from project_forge.constants import SCRIPTS_DIR
from project_forge.get_keyword_mapping import get_variable_mapping
from project_forge.git_commit_helper import commit_with_ps
from project_forge.pipeline.pipeline_context import PipelineContext
from project_forge.replace_variables import replace_variables


def _bool_flag(flag_name: str, value: bool) -> List[str]:
    """Return ['-FlagName'] if value is truthy; otherwise []."""
    return [f"-{flag_name}"] if bool(value) else []


class AddSubmodules(IPipe):
    _default_branch: str = "main"
    _default_recursive: bool = True
    _default_shallow: bool = False
    _default_update: bool = False
    _default_force: bool = False
    _default_timeout_sec: int = 600  # 10 minutes for big repos
    _dry_run_whatif: bool = False    # set True to pass -WhatIf to the PS script

    def __init__(self, logger: HoornLogger):
        self._logger = logger
        self._use_input_helper: UserInputHelper = UserInputHelper(logger, "APP.AddSubmodules")

    def flow(self, data: PipelineContext) -> PipelineContext:
        self._logger.trace("Flowing pipe for submodule add.")
        self._initialize_gitmodules_file(data.repo_path)

        submodules: List[Dict] = []
        variable_mapping = get_variable_mapping(data)

        for template in data.included_templates:
            submodules.extend(self._retrieve_submodules_for_template(template, variable_mapping))
            if data.multi_language:
                submodules.extend(self._retrieve_multi_submodules_for_template(template, variable_mapping))

        submodules.extend(data.framework_submodules)

        commit_with_ps(
            logger=self._logger,
            repo_path=data.repo_path,
            message="Project Forge: Stage 3 -- pre-submodules checkpoint",
            add=["."],
            only_if_changes=True,
        )

        self._initialize_submodules(submodules, data.repo_path)

        commit_with_ps(
            logger=self._logger,
            repo_path=data.repo_path,
            message="Project Forge: Stage 3 -- submodules",
            add=["."],
            only_if_changes=True,
        )

        self._logger.trace("Done flowing pipe for submodule add.")

        return data

    @staticmethod
    def _validate_optional_choice(choice: str) -> Tuple[bool, str]:
        if choice.lower() == "y":
            return True, ""
        if choice.lower() == "n":
            return True, ""
        if len(choice.lower().strip()) == 0 or choice.lower().strip() == "":
            return True, ""

        return False, f"Expected one of 'y'/'n', got: '{choice.lower()}'"

    # noinspection t
    def _initialize_submodules(self, submodules: List[Dict], repo_path: Path) -> None:
        """
        `submodules` supports (per item):
          - name (str)                -> -submoduleName
          - relative_path (str)       -> -submodulePath
          - url (str)                 -> -submoduleUrl
          - optional (bool)           -> (prompt handled by _should_include_optional)
          - branch (str)              -> -Branch           (fallback: self._default_branch)
          - recursive (bool)          -> -Recursive        (fallback: self._default_recursive)
          - shallow (bool)            -> -Shallow          (fallback: self._default_shallow)
          - update (bool)             -> -Update           (fallback: self._default_update)
          - force (bool)              -> -Force            (fallback: self._default_force)
        """
        self._logger.info(
            f"Initializing submodules for project: {repo_path.name}",
            separator="APP.AddModules"
        )

        add_submodule_script: Path = SCRIPTS_DIR.joinpath("add_submodule.ps1").resolve()

        if not add_submodule_script.exists():
            self._logger.error(
                f"Script not found: {add_submodule_script}",
                separator="APP.AddModules"
            )
            return

        # Prefer powershell if available, fallback to pwsh if that's what you use
        ps_exe: Optional[str] = shutil.which("powershell.exe") or shutil.which("pwsh")
        if not ps_exe:
            self._logger.error("PowerShell not found on PATH.", separator="APP.AddModules")
            return

        choice_mapping = {"y": True, "n": False, "": False}

        failures: List[str] = []

        for submodule in submodules:
            name: str = submodule["name"]
            path: str = submodule["relative_path"]
            url: str = submodule["url"]
            optional: bool = submodule.get("optional", False)

            branch: str = submodule.get("branch", self._default_branch)
            recursive: bool = submodule.get("recursive", self._default_recursive)
            shallow: bool = submodule.get("shallow", self._default_shallow)
            update: bool = submodule.get("update", self._default_update)
            force: bool = submodule.get("force", self._default_force)

            if optional:
                should_include = self._should_include_optional(name, choice_mapping)
                if not should_include:
                    self._logger.info(
                        f"Skipping optional submodule: {name}",
                        separator="APP.AddModules"
                    )
                    continue

            self._logger.trace("Checking work tree cleanliness before submodule add...")
            self._print_git_status(repo_path, self._logger)

            # Build PowerShell command
            cmd: List[str] = [
                ps_exe,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy", "Bypass",
                "-File", str(add_submodule_script),
                "-TargetRepoPath", str(repo_path),
                "-SubmoduleName", name,
                "-SubmodulePath", path,
                "-SubmoduleUrl", url,
                "-Branch", branch,
            ]

            if recursive: cmd.append("-Recursive")
            if shallow:   cmd.append("-Shallow")
            if update:    cmd.append("-Update")
            if force:     cmd.append("-Force")

            if self._dry_run_whatif:
                cmd.append("-WhatIf")

            self._logger.info(
                f"Adding submodule '{name}' at '{path}' (branch={branch}, "
                f"recursive={recursive}, shallow={shallow}, update={update}, force={force})",
                separator="APP.AddModules"
            )

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self._default_timeout_sec
                )
            except subprocess.TimeoutExpired:
                msg = f"Timed out adding submodule: {name}"
                self._logger.error(msg, separator="APP.AddModules")
                failures.append(f"{name}: timeout")
                continue
            except Exception as e:
                msg = f"Exception running submodule script for {name}: {e}"
                self._logger.error(msg, separator="APP.AddModules")
                failures.append(f"{name}: exception")
                continue

            # Emit logs
            if result.stdout:
                self._logger.info(result.stdout.strip(), separator="APP.AddModules")

            if result.stderr:
                for line in result.stderr.splitlines():
                    if not line.strip():
                        continue
                    lower = line.lower()
                    if "warning:" in lower:
                        self._logger.warning(line, separator="APP.AddModules")
                    elif "error:" in lower:
                        self._logger.error(line, separator="APP.AddModules")
                    else:
                        self._logger.info(line, separator="APP.AddModules")

            if result.returncode != 0:
                failures.append(f"{name}: exit={result.returncode}")

        if failures:
            self._logger.error(
                "Some submodules failed: " + "; ".join(failures),
                separator="APP.AddModules"
            )
        else:
            self._logger.info(
                f"Submodules added for project: {repo_path.name}",
                separator="APP.AddModules"
            )

    def _should_include_optional(self, submodule_name: str, choice_mapping: Dict[str, bool]) -> bool:
        prompt: str = f"SUBMODULE: {submodule_name}\n\tDo you want to include this submodule in your project? y/n [n]"
        user_choice = self._use_input_helper.get_user_input(
            prompt=prompt,
            validator_func=self._validate_optional_choice,
            expected_response_type=str,
            error_ignores_default=False
        )

        choice: bool | None = choice_mapping.get(user_choice, None)
        if choice is None:
            self._logger.warning(f"Unknown choice: '{user_choice}'. This should not have happened!", separator="APP.AddModules")
            return False
        if not choice:
            return False

        return True

    def _retrieve_submodules_for_template(self, template_folder: Path, variable_mapping: Dict[str, str]) -> List[Dict]:
        self._logger.trace(f"Retrieving submodules for template {template_folder.name}")

        submodule_path = template_folder.joinpath("submodules.json")
        if not submodule_path.is_file():
            self._logger.info(f"Submodules file not found at: {submodule_path} - Skipping", separator="APP")
            return []

        with open(submodule_path, "r") as submodule_file:
            submodule_string = submodule_file.read()
            submodule_string = replace_variables(submodule_string, variable_mapping, self._logger)
            submodules = json.loads(submodule_string)

        self._logger.trace(f"Done retrieving submodules for template {template_folder.name}")
        return submodules

    def _retrieve_multi_submodules_for_template(self, template_folder: Path, variable_mapping: Dict[str, str]) -> List[Dict]:
        self._logger.trace(f"Retrieving multi-submodules for template {template_folder.name}")

        submodule_multi_path = template_folder.joinpath("submodules_multi.json")
        if not submodule_multi_path.is_file():
            self._logger.info(f"Multi-submodules file not found at: {submodule_multi_path} - Skipping", separator="APP")
            return []

        with open(submodule_multi_path, "r") as submodule_file:
            submodule_string = submodule_file.read()
            submodule_string = replace_variables(submodule_string, variable_mapping, self._logger)
            submodules = json.loads(submodule_string)

        self._logger.trace(f"Done retrieving multi-submodules for template {template_folder.name}")
        return submodules

    def _initialize_gitmodules_file(self, project_path: Path) -> None:
        self._logger.trace("Initializing gitmodules file")
        gitmodules = project_path / ".gitmodules"
        if not gitmodules.exists():
            with gitmodules.open("w", encoding="utf-8", newline="\n") as f:
                f.write("")
        self._logger.trace("Done initializing gitmodules file")

    @staticmethod
    def _print_git_status(repo_path: Path, logger: HoornLogger) -> None:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_path), "status", "--porcelain", "--ignored"],
                capture_output=True, text=True, check=False
            )
            if result.stdout.strip():
                logger.warning("Git status before submodule add:\n" + result.stdout.strip(),
                               separator="APP.AddModules")
            else:
                logger.info("Git status clean before submodule add.", separator="APP.AddModules")
        except Exception as e:
            logger.error(f"Failed to run git status: {e}", separator="APP.AddModules")
