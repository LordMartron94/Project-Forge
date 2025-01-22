import shutil

from project_forge.common.py_common.logging import HoornLogger
from project_forge.common.py_common.patterns import IPipe
from project_forge.model.config_model import ConfigModel
from project_forge.pipeline.pipeline_context import PipelineContext


class CopyRouterBinary(IPipe):
    def __init__(self, logger: HoornLogger, configuration: ConfigModel):
        self._logger = logger
        self._configuration = configuration

    def flow(self, data: PipelineContext) -> PipelineContext:
        latest_binary = self._configuration.latest_router_exe

        self._logger.trace(f"Copying router binary from: {latest_binary}", separator="APP")

        destination_binary = data.repo_path.joinpath("router").joinpath("router.exe")
        destination_binary.parent.mkdir(parents=True, exist_ok=True)

        shutil.copyfile(src=latest_binary, dst=destination_binary)
        self._logger.debug("Router binary copied successfully.", separator="APP")
        return data
