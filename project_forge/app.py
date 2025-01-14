import json
import shutil
import subprocess
from pathlib import Path
from typing import List

from common.py_common.logging import HoornLogger
from common.py_common.cli_framework import CommandLineInterface
from project_forge.common.py_common.handlers import FileHandler
from project_forge.common.py_common.user_input.user_input_helper import UserInputHelper
from project_forge.constants import SUPPORTED_LANGUAGES, PROJECT_ROOT
from project_forge.model.config_model import ConfigModel
from project_forge.pipeline.forge_pipeline import ForgePipeline
from project_forge.pipeline.pipeline_context import PipelineContext

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


	def _initialize_project(self):
		project_path: Path = self._get_desired_project_from_user()
		root_project_name = project_path.name
		root_project_name = root_project_name.replace(" ", "_")
		root_project_name = root_project_name.replace("-", "_")
		root_project_name = root_project_name.lower()

		languages: List[str] = self._get_desired_languages_from_user()
		template_folders: List[Path] = self._get_template_folders(languages)
		multi_language = len(languages) > 1

		context: PipelineContext = PipelineContext(
			project_path=project_path,
			root_project_path=project_path.joinpath(root_project_name),
			included_templates=template_folders,
			submodule_root_name=root_project_name + "/components/",
			project_root_name=root_project_name,
			multi_language=multi_language,
		)

		pipeline: ForgePipeline = ForgePipeline(self._logger, self._configuration, multi_language)
		pipeline.build_pipeline()
		pipeline.flow(context)

		self._logger.info(f"Project initialized successfully in: {project_path}", separator="APP")

	def run(self):
		self._cli.start_listen_loop()

