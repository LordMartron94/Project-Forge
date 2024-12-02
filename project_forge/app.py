from pathlib import Path
from typing import List

from common.py_common.logging import HoornLogger
from common.py_common.cli_framework import CommandLineInterface
from project_forge.common.py_common.handlers import FileHandler
from project_forge.common.py_common.user_input.user_input_helper import UserInputHelper
from project_forge.model.config_model import ConfigModel


class App:
	def __init__(self, logger: HoornLogger, configuration: ConfigModel):
		self._logger: HoornLogger = logger
		self._configuration: ConfigModel = configuration

		self._cli: CommandLineInterface = CommandLineInterface(self._logger)
		self._user_input_handler: UserInputHelper = UserInputHelper(self._logger)
		self._file_handler: FileHandler = FileHandler()

	def get_project_paths(self) -> List[Path]:
		self._file_handler.get_children_directories(self._configuration.project_dir)

	def run(self):
		self._cli.start_listen_loop()

