import json
import shutil
import subprocess
from pathlib import Path
from typing import List

from common.py_common.logging import HoornLogger
from common.py_common.cli_framework import CommandLineInterface
from project_forge.common.py_common.handlers import FileHandler
from project_forge.common.py_common.user_input.user_input_helper import UserInputHelper
from project_forge.constants import SUPPORTED_LANGUAGES, PROJECT_ROOT, SCRIPTS_DIR
from project_forge.model.config_model import ConfigModel


class App:
	def __init__(self, logger: HoornLogger, configuration: ConfigModel):
		self._logger: HoornLogger = logger
		self._configuration: ConfigModel = configuration

		self._cli: CommandLineInterface = CommandLineInterface(self._logger)
		self._user_input_handler: UserInputHelper = UserInputHelper(self._logger)
		self._file_handler: FileHandler = FileHandler()
		self._initialize_commands()

	def _initialize_commands(self):
		self._cli.add_command(["initialize-project", "ip"], description="Initialize a project with the correct structure.", action=self._initialize_project)

	def _get_project_paths(self) -> List[Path]:
		return self._file_handler.get_children_directories(self._configuration.project_dir)

	def _get_desired_project_from_user(self):
		paths = self._get_project_paths()

		paths.sort(key=lambda x: x.name.lower())
		possible_projects = [path.name for path in paths]

		def __validate_input(input_value: int) -> [bool, str]:
			valid: bool = 1 <= input_value <= len(possible_projects)

			if not valid:
				return False, "Please enter a number between 1 and " + str(len(possible_projects))
			else: return True, ""

		for i, project in enumerate(possible_projects):
			print(f"{i+1}) {project}")

		choice = self._user_input_handler.get_user_input("Enter the number of the project you want to initialize (1-" + str(len(possible_projects)) + "):", expected_response_type=int, validator_func=__validate_input)
		return paths[choice-1]

	def _get_desired_languages_from_user(self) -> List[str]:
		supported_languages = [language["name"] for language in SUPPORTED_LANGUAGES]
		templates = [language["template_folder"] for language in SUPPORTED_LANGUAGES]

		def __validate_input(input_value: str) -> [bool, str]:
			choices: List[int] = [int(num) for num in input_value.split()]

			valid: bool = all(1 <= choice <= len(supported_languages) for choice in choices)

			if not valid:
				return False, "Please enter a number between 1 and " + str(len(supported_languages)) + " separated by spaces."

			return True, ""

		for i, language in enumerate(supported_languages):
			print(f"{i+1}) {language}")

		choice = self._user_input_handler.get_user_input("Enter the numbers of the programming languages you want to include (separated by spaces):", expected_response_type=str, validator_func=__validate_input)
		return [templates[choice-1] for choice in [int(num) for num in choice.split()]]

	def _get_template_folders(self, languages: List[str]) -> List[Path]:
		root_template_dir = PROJECT_ROOT.joinpath("templates")

		return [root_template_dir.joinpath("default")] + [root_template_dir.joinpath(language) for language in languages]

	def _copy_router_binary(self, project_path: Path):
		latest_binary = self._configuration.latest_router_exe
		destination_binary = project_path.joinpath("router").joinpath("router.exe")
		destination_binary.parent.mkdir(parents=True, exist_ok=True)

		self._logger.debug(f"Copying router binary from: {latest_binary}", separator="APP")

		shutil.copyfile(src=latest_binary, dst=destination_binary)
		self._logger.debug("Router binary copied successfully.", separator="APP")

	def _copy_utility_scripts(self, project_path: Path):
		destination = project_path.joinpath("scripts")
		destination.parent.mkdir(parents=True, exist_ok=True)

		self._logger.debug(f"Copying utility scripts to: {project_path}", separator="APP")
		shutil.copytree(src=SCRIPTS_DIR, dst=destination)
		self._logger.debug("Utility scripts copied successfully.", separator="APP")

	def _initialize_repo_structure(self, project_path: Path):
		self._logger.debug(f"Initializing project structure in: {project_path}", separator="APP")

		root_project_name = project_path.name
		root_project_name = root_project_name.replace(" ", "_")
		root_project_name = root_project_name.replace("-", "_")
		root_project_name = root_project_name.lower()
		root_project_path = project_path.joinpath(root_project_name)

		project_path.joinpath("build").mkdir(parents=True, exist_ok=True)

		root_project_path.mkdir(parents=True, exist_ok=True)

		folders_to_create = ["components", "tests", "benchmarks", "docs"]

		for folder in folders_to_create:
			root_project_path.joinpath(folder).mkdir(parents=True, exist_ok=True)

		self._logger.debug("Project structure initialized successfully.", separator="APP")

	def _create_combined_gitignore(self, project_path: Path, chosen_templates: List[Path]):
		self._logger.debug(f"Creating combined gitignore in: {project_path}", separator="APP")

		with open(project_path.joinpath(".gitignore"), "w") as gitignore_file:
			for template_folder in chosen_templates:
				gitignore_path = template_folder.joinpath("gitignore.txt")

				if not gitignore_path.is_file():
					self._logger.warning(f"Gitignore file not found at: {gitignore_path} - Skipping", separator="APP")
					continue

				with open(gitignore_path, "r") as template_gitignore_file:
					content = template_gitignore_file.read()
					gitignore_file.write(content)
					gitignore_file.write("\n\n")

		self._logger.debug("Combined gitignore created successfully.", separator="APP")

	def _add_submodules(self, project_path: Path, chosen_templates: List[Path]):
		# Initialize .gitmodules file
		project_path.joinpath(".gitmodules").touch()
		add_submodule_script = SCRIPTS_DIR.joinpath("add_submodule.ps1").resolve()

		for template_folder in chosen_templates:
			submodule_path = template_folder.joinpath("submodules.json")
			if not submodule_path.is_file():
				self._logger.info(f"Submodules file not found at: {submodule_path} - Skipping", separator="APP")
				continue
			submodules = json.load(open(submodule_path))
			for submodule in submodules:
				name = submodule["name"]
				path = submodule["relative_path"]
				url = submodule["url"]

				command = [
					"powershell.exe",
					"-File", add_submodule_script,
					"-submoduleName", name,
					"-submodulePath", path,
					"-submoduleUrl", url
				]

				result = subprocess.run(command, capture_output=True, text=True)
				self._logger.info(result.stdout, separator="APP.AddModules")
				if result.returncode != 0:
					self._logger.error(f"Failed to add submodule: {name} - {result.stderr}", separator="APP.AddModules")


	def _initialize_project(self):
		project_path: Path = self._get_desired_project_from_user()
		languages: List[str] = self._get_desired_languages_from_user()
		template_folders: List[Path] = self._get_template_folders(languages)

		# if len(languages) > 1:
		# 	self._copy_router_binary(project_path)

		# self._copy_utility_scripts(project_path)
		# self._create_combined_gitignore(project_path, template_folders)
		# self._initialize_repo_structure(project_path)
		self._add_submodules(project_path, template_folders)

		self._logger.info(f"Project initialized successfully in: {project_path}", separator="APP")

	def run(self):
		self._cli.start_listen_loop()

