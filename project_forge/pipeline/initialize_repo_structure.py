import json
import re
from pathlib import Path
from typing import Dict, Any, List

from project_forge.common.py_common.logging import HoornLogger
from project_forge.common.py_common.patterns import IPipe
from project_forge.constants import PROJECT_ROOT
from project_forge.pipeline.pipeline_context import PipelineContext


class InitializeRepoStructure(IPipe):
    """
    Initializes the repository structure by creating directories and files
    based on a default and language-specific configuration files.
    """

    def __init__(self, logger: HoornLogger):
        self._logger = logger
        self._keyword_mapping: Dict[str, str] = {}

    def flow(self, data: PipelineContext) -> PipelineContext:
        """
        Executes the logic to initialize the repository structure.
        """
        self._logger.debug(f"Initializing project structure in: {data.repo_path}", separator="APP")

        self._build_keyword_mapping(data)

        final_structure = self._get_final_structure(data.included_templates)

        self._create_folders(data.repo_path, final_structure.get("folders", []))
        self._create_files(data, final_structure.get("files", []))

        if data.multi_language:
            self._create_multi_language_files(data)

        self._logger.debug("Project structure initialized successfully.", separator="APP")
        return data

    def _build_keyword_mapping(self, data: PipelineContext):
        """
        Builds the keyword mapping dictionary with all supported variables.
        """
        version_parts = data.project_version.split('.')
        self._keyword_mapping = {
            "${PROJECT_NAME}": data.project_root_name_sanitized,
            "${PROJECT_NAME_UPPER}": data.project_root_name_sanitized.upper(),
            "${SANITIZED_NAME}": data.project_root_name_sanitized,
            "${ROOT_FOLDER_NAME}": data.project_root_name,
            "${GIT_URL}": data.git_url,
            "${PROJECT_VERSION}": data.project_version,
            "${PROJECT_VERSION_MAJOR}": version_parts[0] if len(version_parts) > 0 else "0",
            "${PROJECT_VERSION_MINOR}": version_parts[1] if len(version_parts) > 1 else "0",
            "${PROJECT_VERSION_PATCH}": version_parts[2] if len(version_parts) > 2 else "0",
            "${CMAKE_CURRENT_SOURCE_DIR}": "${CMAKE_CURRENT_SOURCE_DIR}",
            "${CMAKE_CURRENT_BINARY_DIR}": "${CMAKE_CURRENT_BINARY_DIR}",
            "${CMAKE_CURRENT_LIST_DIR}": "${CMAKE_CURRENT_LIST_DIR}",
        }

    def _replace_variables(self, input_string: str) -> str:
        """
        Replaces known variables in a string and warns about unsupported ones.
        """
        # Find all potential variables
        potential_vars = re.findall(r"\$\{.*?}", input_string)
        for var in potential_vars:
            if var not in self._keyword_mapping:
                self._logger.warning(f"Unsupported variable found: '{var}'", separator="APP")

        # Replace known variables
        for key, value in self._keyword_mapping.items():
            input_string = input_string.replace(key, value)
        return input_string

    def _get_final_structure(self, template_paths: List[Path]) -> Dict[str, Any]:
        """
        Loads the default structure and merges it with language-specific structures.
        If any language provides a structure.json, the default is ignored.
        """
        default_template_path = template_paths[0]
        language_templates_with_structure = [
            p for p in template_paths[1:]
            if p.joinpath("structure.json").is_file()
        ]

        final_structure = {}
        if not language_templates_with_structure:
            self._logger.debug("No language-specific structure found, using default.", separator="APP")
            final_structure = self._load_structure(default_template_path.joinpath("structure.json"), default_template_path)
        else:
            for template_path in language_templates_with_structure:
                structure_file = template_path.joinpath("structure.json")
                self._logger.debug(f"Found structure file at: {structure_file}", separator="APP")
                language_structure = self._load_structure(structure_file, template_path)
                final_structure = self._merge_structures(final_structure, language_structure)

        return final_structure

    def _create_folders(self, project_path: Path, folders: List[str]):
        """
        Creates the directory structure for the project.
        """
        for folder in folders:
            processed_folder = self._replace_variables(folder)
            (project_path / processed_folder).mkdir(parents=True, exist_ok=True)

    def _create_files(self, data: PipelineContext, files: List[Dict[str, str]]):
        """
        Copies and processes template files into the project structure.
        """
        for file_info in files:
            source_path = Path(file_info["template_path"]).joinpath(file_info["source"])
            destination_path_str = self._replace_variables(file_info["destination"])
            destination_path = data.repo_path.joinpath(destination_path_str)

            if not source_path.is_file():
                self._logger.warning(f"Template file not found at: {source_path}", separator="APP")
                continue

            with open(source_path, "r") as f:
                content = f.read()

            processed_content = self._replace_variables(content)

            destination_path.parent.mkdir(parents=True, exist_ok=True)
            with open(destination_path, "w") as f:
                f.write(processed_content)

    def _create_multi_language_files(self, data: PipelineContext):
        """
        Creates files specific to multi-language projects.
        """
        # Create requirements.txt
        with open(data.project_path.joinpath("requirements.txt"), "w") as f:
            f.write("-r components/MD.Logging/requirements.txt\n")

        # Create launch_config.json
        default_config_path = PROJECT_ROOT.joinpath("_internal/default_launcher_config.json")
        with open(default_config_path, "r") as f:
            default_contents = f.read()
        processed_contents = self._replace_variables(default_contents)
        with open(data.repo_path.joinpath("launch_config.json"), "w") as f:
            f.write(processed_contents)

        # Create todo.txt
        with open(data.repo_path.joinpath("todo.txt"), "w") as f:
            f.write(
                "Delete this file when you have executed the following: "
                "create a symlink between the venv folder and your project root folder.\n\n"
                "This way, the launcher script will work correctly."
            )

    @staticmethod
    def _load_structure(path: Path, template_path: Path) -> Dict[str, Any]:
        """
        Loads a structure configuration file and injects the template_path into file info.
        """
        if path.is_file():
            with open(path, "r") as f:
                structure = json.load(f)
                if "files" in structure:
                    for file_info in structure["files"]:
                        file_info["template_path"] = template_path
                return structure
        return {}

    # noinspection t
    @staticmethod
    def _merge_structures(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges two structure configurations.
        """
        merged = base.copy()
        for key, value in override.items():
            if key in merged and isinstance(merged[key], list) and isinstance(value, list):
                for item in value:
                    if item not in merged[key]:
                        merged[key].append(item)
            else:
                merged[key] = value
        return merged
