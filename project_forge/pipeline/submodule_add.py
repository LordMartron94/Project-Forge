import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

from project_forge.common.py_common.logging import HoornLogger
from project_forge.common.py_common.patterns import IPipe
from project_forge.common.py_common.user_input.user_input_helper import UserInputHelper
from project_forge.constants import SCRIPTS_DIR
from project_forge.pipeline.pipeline_context import PipelineContext


class AddSubmodules(IPipe):
    def __init__(self, logger: HoornLogger):
        self._logger = logger
        self._use_input_helper: UserInputHelper = UserInputHelper(logger, "APP.AddSubmodules")

    def flow(self, data: PipelineContext) -> PipelineContext:
        self._logger.trace("Flowing pipe for submodule add.")
        self._initialize_gitmodules_file(data.repo_path)

        submodules: List[Dict] = []

        for template in data.included_templates:
            submodules.extend(self._retrieve_submodules_for_template(template))
            if data.multi_language:
                submodules.extend(self._retrieve_multi_submodules_for_template(template))

        submodules.extend(data.framework_submodules)

        self._initialize_submodules(submodules, data.submodule_root_name, data.repo_path)
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
    def _initialize_submodules(self, submodules: List[Dict], submodule_root_name: str, project_path: Path) -> None:
        self._logger.info(f"Initializing submodules for project: {project_path.name}", separator="APP.AddModules")
        add_submodule_script = SCRIPTS_DIR.joinpath("add_submodule.ps1").resolve()

        choice_mapping = {
            "y": True,
            "n": False,
            "": False
        }

        for submodule in submodules:
            name = submodule["name"]
            path = submodule_root_name + submodule["relative_path"]
            url = submodule["url"]
            optional = submodule.get("optional", False)

            if optional:
                should_include = self._should_include_optional(name, choice_mapping)
                if not should_include:
                    continue

            command = [
                "powershell.exe",
                "-File", add_submodule_script,
                "-targetRepoPath", project_path,
                "-submoduleName", name,
                "-submodulePath", path,
                "-submoduleUrl", url
            ]

            result = subprocess.run(command, capture_output=True, text=True)
            self._logger.info(result.stdout, separator="APP.AddModules")
            if result.returncode != 0:
                self._logger.error(f"Failed to add submodule: {name} - {result.stderr}", separator="APP.AddModules")

        self._logger.info(f"Submodules added for project: {project_path.name}", separator="APP.AddModules")

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

    def _retrieve_submodules_for_template(self, template_folder: Path) -> List[Dict]:
        self._logger.trace(f"Retrieving submodules for template {template_folder.name}")

        submodule_path = template_folder.joinpath("submodules.json")
        if not submodule_path.is_file():
            self._logger.info(f"Submodules file not found at: {submodule_path} - Skipping", separator="APP")
            return []
        submodules = json.load(open(submodule_path))

        self._logger.trace(f"Done retrieving submodules for template {template_folder.name}")
        return submodules

    def _retrieve_multi_submodules_for_template(self, template_folder: Path) -> List[Dict]:
        self._logger.trace(f"Retrieving multi-submodules for template {template_folder.name}")

        submodule_multi_path = template_folder.joinpath("submodules_multi.json")
        if not submodule_multi_path.is_file():
            self._logger.info(f"Multi-submodules file not found at: {submodule_multi_path} - Skipping", separator="APP")
            return []
        submodule_multi = json.load(open(submodule_multi_path))

        self._logger.trace(f"Done retrieving multi-submodules for template {template_folder.name}")
        return submodule_multi

    def _initialize_gitmodules_file(self, project_path: Path) -> None:
        self._logger.trace("Initializing gitmodules file")
        project_path.joinpath(".gitmodules").touch()
        self._logger.trace("Done initializing gitmodules file")

