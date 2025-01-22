import shutil

from project_forge.common.py_common.logging import HoornLogger
from project_forge.common.py_common.patterns import IPipe
from project_forge.constants import SCRIPTS_DIR
from project_forge.pipeline.pipeline_context import PipelineContext


class CopyUtilityScripts(IPipe):
    def __init__(self, logger: HoornLogger):
        self._logger = logger

    def flow(self, data: PipelineContext) -> PipelineContext:
        destination = data.repo_path.joinpath("scripts")
        destination.parent.mkdir(parents=True, exist_ok=True)

        self._logger.trace(f"Copying utility scripts to: {data.repo_path}", separator="APP")
        shutil.copytree(src=SCRIPTS_DIR, dst=destination)
        self._logger.debug("Utility scripts copied successfully.", separator="APP")
        return data
