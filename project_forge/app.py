from pathlib import Path
from typing import List, Tuple

from common.py_common.cli_framework import CommandLineInterface
from common.py_common.logging import HoornLogger
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
		self._cli.add_command(
			["initialize-project", "ip"],
			description="Initialize a project with the correct structure.",
			action=self._initialize_project
		)

	def _get_project_paths(self) -> List[Path]:
		return self._file_handler.get_children_directories(self._configuration.project_dir)

	def _get_desired_project_from_user(self):
		paths = self._get_project_paths()
		paths.sort(key=lambda x: x.name.lower())
		possible_projects = [path.name for path in paths]

		def __validate_input(input_value: int) -> [bool, str]:
			is_valid: bool = 1 <= input_value <= len(possible_projects)
			error_msg = f"Please enter a number between 1 and {len(possible_projects)}."
			return (is_valid, "") if is_valid else (False, error_msg)

		print("Please select a project to initialize:")
		for i, project in enumerate(possible_projects):
			print(f"  {i+1}) {project}")

		prompt = f"\nEnter the number of the project (1-{len(possible_projects)}):"
		choice = self._user_input_handler.get_user_input(
			prompt,
			expected_response_type=int,
			validator_func=__validate_input
		)
		return paths[choice - 1]

	# noinspection t
	def _get_desired_languages_from_user(self) -> List[str]:
		"""
		Presents a formatted, grouped list of languages to the user and returns their selections.
		"""
		all_languages = [
			lang for group in SUPPORTED_LANGUAGES
			for lang in group.get('languages', [])
		]
		total_languages = len(all_languages)

		def __validate_input(input_value: str) -> [bool, str]:
			if not input_value.strip():
				return False, "Input cannot be empty. Please enter numbers separated by spaces."
			try:
				choices: List[int] = [int(num) for num in input_value.split()]
			except ValueError:
				return False, "Invalid input. Please enter only numbers separated by spaces."

			is_valid: bool = all(1 <= choice <= total_languages for choice in choices)
			error_msg = f"Please ensure all numbers are between 1 and {total_languages}."
			return (is_valid, "") if is_valid else (False, error_msg)

		# --- Display Logic ---
		print("Select the programming languages you want to include:")
		counter = 1
		for group in SUPPORTED_LANGUAGES:
			# Only display groups that contain languages
			if group.get('languages'):
				print(f"\n--- {group['group_name']} ---")
				print(f"    {group['description']}")
				for language in group['languages']:
					print(f"  {counter}) {language['name']}")
					counter += 1

		# --- Input and Processing Logic ---
		prompt = f"\nEnter the numbers of the languages (1-{total_languages}), separated by spaces:"
		choice_str = self._user_input_handler.get_user_input(
			prompt,
			expected_response_type=str,
			validator_func=__validate_input
		)

		# Convert 1-based user input to 0-based indices and retrieve template folders
		chosen_indices = [int(num) - 1 for num in choice_str.split()]
		return [all_languages[i]['template_folder'] for i in chosen_indices]


	def _get_template_folders(self, languages: List[str]) -> List[Path]:
		root_template_dir = PROJECT_ROOT.joinpath("templates")
		default_template = root_template_dir.joinpath("default")
		language_templates = [root_template_dir.joinpath(lang) for lang in languages]
		return [default_template] + language_templates

	@staticmethod
	def _validate_optional_choice(choice: str) -> Tuple[bool, str]:
		if choice.lower() == "y":
			return True, ""
		if choice.lower() == "n":
			return True, ""
		if len(choice.lower().strip()) == 0 or choice.lower().strip() == "":
			return True, ""

		return False, f"Expected one of 'y'/'n', got: '{choice.lower()}'"

	def _initialize_project(self):
		project_path: Path = self._get_desired_project_from_user()

		# Sanitize project name for use in file names, etc.
		sanitized_name = project_path.name.replace(" ", "_").replace("-", "_").replace(".", "_").lower()

		languages: List[str] = self._get_desired_languages_from_user()
		template_folders: List[Path] = self._get_template_folders(languages)
		multi_language = len(languages) > 1

		git_url = f"https://github.com/LordMartron94/{project_path.name}"
		choice: str = self._user_input_handler.get_user_input(
			f"Is '{git_url}' the correct git URL? y/n [y]",
			expected_response_type=str,
			validator_func=self._validate_optional_choice
		)

		mapping = {
			"y": True,
			"n": False,
			"": True
		}

		is_right_url: bool | None = mapping.get(choice, None)

		if is_right_url is None:
			self._logger.warning(f"This should not have happened, unknown choice: '{choice}'", separator="APP")
			is_right_url = False

		if not is_right_url:
			git_url = self._user_input_handler.get_user_input(
				"Enter the correct GIT URL.",
				expected_response_type=str,
				validator_func=lambda c: (True, "")
			)

		context: PipelineContext = PipelineContext(
			repo_path=project_path,
			project_path=project_path.joinpath(sanitized_name),
			included_templates=template_folders,
			project_root_name=project_path.name,
			project_root_name_sanitized=sanitized_name,
			multi_language=multi_language,
			git_url=git_url,
			project_version="0.0.0"
		)

		pipeline: ForgePipeline = ForgePipeline(
			self._logger,
			self._user_input_handler,
			self._configuration,
			multi_language
		)
		pipeline.build_pipeline()
		pipeline.flow(context)

		self._logger.info(f"Project initialized successfully in: {project_path}", separator="APP")

	def run(self):
		self._cli.start_listen_loop()
