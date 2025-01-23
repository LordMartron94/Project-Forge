import json
import subprocess
from pathlib import Path
from typing import List, Dict

from project_forge.common.py_common.logging import HoornLogger
from project_forge.common.py_common.patterns import IPipe
from project_forge.constants import SCRIPTS_DIR
from project_forge.pipeline.pipeline_context import PipelineContext


class AddSubmodules(IPipe):
    def __init__(self, logger: HoornLogger):
        self._logger = logger

    def flow(self, data: PipelineContext) -> PipelineContext:
        self._logger.trace("Flowing pipe for submodule add.")
        self._initialize_gitmodules_file(data.repo_path)

        submodules: List[Dict] = []

        for template in data.included_templates:
            submodules.extend(self._retrieve_submodules_for_template(template))
            if data.multi_language:
                submodules.extend(self._retrieve_multi_submodules_for_template(template))

        submodules.extend(data.extra_submodules)

        self._initialize_submodules(submodules, data.submodule_root_name, data.repo_path)
        self._logger.trace("Done flowing pipe for submodule add.")

        return data

    def _initialize_submodules(self, submodules: List[Dict], submodule_root_name: str, project_path: Path) -> None:
        self._logger.info(f"Initializing submodules for project: {project_path.name}", separator="APP.AddModules")
        add_submodule_script = SCRIPTS_DIR.joinpath("add_submodule.ps1").resolve()

        for submodule in submodules:
            name = submodule["name"]
            path = submodule_root_name + submodule["relative_path"]
            url = submodule["url"]

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

