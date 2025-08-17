import json
import os
import shutil
from pathlib import Path

from app import App
from common.py_common.logging import HoornLogger
from project_forge.common.py_common.logging import HoornLoggerBuilder, LogType
from project_forge.constants import PROJECT_ROOT
from project_forge.model.config_model import ConfigModel

def get_config_dir(application_name: str):
	"""Gets the configuration directory.

    Returns:
      The configuration directory.
    """

	try:
		user_config_dir = os.path.expanduser("~")
	except Exception as e:
		raise e

	dir = os.path.join(user_config_dir, "AppData", "Local")
	config_dir = os.path.join(dir, application_name, "config")
	return config_dir

def get_config_file(application_name: str, logger: HoornLogger) -> Path:
	config_dir = get_config_dir(application_name)
	file = Path(os.path.join(config_dir, "config.json"))

	if not file.is_file():
		logger.warning("Configuration file not found. Creating one.", separator="MAIN")
		default_config_path = PROJECT_ROOT.joinpath("_internal", "default_config.json")

		os.makedirs(config_dir, exist_ok=True)
		shutil.copyfile(src=default_config_path, dst=file)

		logger.info(f"Default configuration file created at: '{file}'", separator="MAIN")
		logger.warning("Make sure to update the configuration file with your desired settings. Before relaunching the app.", separator="MAIN")
		exit(0)

	return file

if __name__ == "__main__":
	max_separator_length = 30

	logger_builder: HoornLoggerBuilder = HoornLoggerBuilder(
		application_name_sanitized="ProjectForge",
		max_separator_length=max_separator_length,
	)

	logger: HoornLogger = logger_builder.build_console_output().get_logger(min_level=LogType.DEBUG)

	config_file = get_config_file("Project Forge", logger)
	content = config_file.read_text()
	content = content.replace("\\", "\\\\")

	data = json.loads(content)

	# Now create the ConfigModel instance
	config: ConfigModel = ConfigModel(**data)

	app: App = App(logger, config)
	app.run()
