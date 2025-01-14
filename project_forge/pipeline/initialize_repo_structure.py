from project_forge.common.py_common.logging import HoornLogger
from project_forge.common.py_common.patterns import IPipe
from project_forge.constants import PROJECT_ROOT
from project_forge.pipeline.pipeline_context import PipelineContext


class InitializeRepoStructure(IPipe):
    def __init__(self, logger: HoornLogger):
        self._logger = logger

    def flow(self, data: PipelineContext) -> PipelineContext:
        self._logger.debug(f"Initializing project structure in: {data.project_path}", separator="APP")
        data.project_path.joinpath("build").mkdir(parents=True, exist_ok=True)

        data.root_project_path.mkdir(parents=True, exist_ok=True)

        folders_to_create = ["components", "tests", "benchmarks", "docs"]

        for folder in folders_to_create:
            data.root_project_path.joinpath(folder).mkdir(parents=True, exist_ok=True)

        if data.multi_language:
            with open(data.root_project_path.joinpath("requirements.txt"), "w") as requirements_file:
                requirements_file.write(f"""
-r components/MD.Logging/requirements.txt
				""")
            with open(data.project_path.joinpath("launch_config.json"), "w") as launch_config_file:
                default_contents = PROJECT_ROOT.joinpath("_internal/default_launcher_config.json").read_text()
                launch_config_file.write(default_contents)
            with open(data.project_path.joinpath("todo.txt"), "w") as todo_file:
                todo_file.write("Delete this file when you have executed the following: create a symlink between the venv folder and your project root folder.\n\nThis way, the launcher script will work correctly.")

        self._logger.debug("Project structure initialized successfully.", separator="APP")

        return data