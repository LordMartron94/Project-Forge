from pathlib import Path

from project_forge.common.py_common.logging import HoornLogger
from project_forge.common.py_common.patterns import IPipe
from project_forge.pipeline.pipeline_context import PipelineContext


class GitIgnoreAdd(IPipe):
    def __init__(self, logger: HoornLogger):
        self._logger = logger

    def flow(self, data: PipelineContext) -> PipelineContext:
        self._logger.debug(f"Creating combined gitignore in: {data.repo_path}", separator="APP")

        gitignore_path: Path = data.repo_path.joinpath(".gitignore")

        with open(gitignore_path, "w") as gitignore_file:
            for template_folder in data.included_templates:
                gitignore_path = template_folder.joinpath("gitignore.txt")

                if not gitignore_path.is_file():
                    self._logger.warning(f"Gitignore file not found at: {gitignore_path} - Skipping", separator="APP")
                    continue

                with open(gitignore_path, "r") as template_gitignore_file:
                    content = template_gitignore_file.read()
                    gitignore_file.write(content)
                    gitignore_file.write("\n\n")

        self._logger.debug("Combined gitignore created successfully.", separator="APP")
        return data
