import json
import shutil
from pathlib import Path
from typing import Dict, Any, List

from project_forge.common.py_common.logging import HoornLogger
from project_forge.common.py_common.patterns import IPipe
from project_forge.configure_repo import enforce_eol_policy
from project_forge.constants import PROJECT_ROOT, INTERNAL_PATH
from project_forge.get_keyword_mapping import get_variable_mapping
from project_forge.git_commit_helper import commit_with_ps
from project_forge.pipeline.pipeline_context import PipelineContext
from project_forge.replace_variables import replace_variables


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

        self._add_git_attributes_and_enforce_eol(data)

        self._build_keyword_mapping(data)

        final_structure = self._get_final_structure(data.included_templates)

        self._create_folders(data.repo_path, final_structure.get("folders", []))
        self._create_files(data, final_structure.get("files", []))

        if data.multi_language:
            self._create_multi_language_files(data)

        # Single consolidated commit (includes structure + any staged renormalized files)
        commit_with_ps(
            logger=self._logger,
            repo_path=data.repo_path,
            message="Project Forge: Stage 1 -- repository structure",
            add=["."],
            only_if_changes=True,
        )

        self._logger.debug("Project structure initialized successfully.", separator="APP")
        return data

    def _build_keyword_mapping(self, data: PipelineContext):
        """
        Builds the keyword mapping dictionary with all supported variables.
        """
        self._keyword_mapping = get_variable_mapping(data)

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
            processed_folder = replace_variables(folder, self._keyword_mapping, self._logger)
            (project_path / processed_folder).mkdir(parents=True, exist_ok=True)

    def _create_files(self, data: PipelineContext, files: List[Dict[str, str]]):
        """
        Copies and processes template files into the project structure.
        """
        for file_info in files:
            source_path = Path(file_info["template_path"]).joinpath(file_info["source"])
            destination_path_str = replace_variables(file_info["destination"], self._keyword_mapping, self._logger)
            destination_path = data.repo_path.joinpath(destination_path_str)

            if not source_path.is_file():
                self._logger.warning(f"Template file not found at: {source_path}", separator="APP")
                continue

            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()

            processed_content = replace_variables(content, self._keyword_mapping, self._logger)

            destination_path.parent.mkdir(parents=True, exist_ok=True)
            # Write with LF newlines to avoid accidental CRLF (Git still normalizes on commit)
            with open(destination_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(processed_content)

    def _create_multi_language_files(self, data: PipelineContext):
        """
        Creates files specific to multi-language projects.
        """
        # Create requirements.txt
        with open(data.project_path.joinpath("requirements.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write("-r components/MD.Logging/requirements.txt\n")

        # Create launch_config.json
        default_config_path = PROJECT_ROOT.joinpath("_internal/default_launcher_config.json")
        with open(default_config_path, "r", encoding="utf-8") as f:
            default_contents = f.read()
        processed_contents = replace_variables(default_contents, self._keyword_mapping, self._logger)
        with open(data.repo_path.joinpath("launch_config.json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(processed_contents)

        # Create todo.txt
        with open(data.repo_path.joinpath("todo.txt"), "w", encoding="utf-8", newline="\n") as f:
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
            with open(path, "r", encoding="utf-8") as f:
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

    def _add_git_attributes_and_enforce_eol(self, data: PipelineContext):
        """
        Copy .gitattributes and immediately enforce EOL policy:
          - Set repo-local git config (autocrlf=input, eol=lf, safecrlf=true)
          - Install pre-commit hook (respects .gitattributes via git check-attr)
          - Renormalize to stage any needed changes (commit happens later)
        """
        output_path = data.repo_path / ".gitattributes"
        shutil.copyfile(INTERNAL_PATH / "git_attributes.txt", output_path)

        # Enforce EOL policy and install hook; stage normalization but don't commit yet.
        enforce_eol_policy(
            logger=self._logger,
            repo_path=data.repo_path,
            commit=False,
        )
