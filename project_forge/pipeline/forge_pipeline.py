from project_forge.common.py_common.logging import HoornLogger
from project_forge.common.py_common.patterns import AbPipeline
from project_forge.model.config_model import ConfigModel
from project_forge.pipeline.copy_router_binary import CopyRouterBinary
from project_forge.pipeline.copy_utility_scripts import CopyUtilityScripts
from project_forge.pipeline.gitignore_add import GitIgnoreAdd
from project_forge.pipeline.initialize_repo_structure import InitializeRepoStructure
from project_forge.pipeline.launch_script_add import AddLaunchScript
from project_forge.pipeline.submodule_add import AddSubmodules


class ForgePipeline(AbPipeline):
    def __init__(self, logger: HoornLogger, configuration: ConfigModel, multi_language: bool):
        self._logger = logger
        self._configuration = configuration
        self._multi_language = multi_language
        super().__init__()

    def build_pipeline(self):
        self._add_step(CopyUtilityScripts(self._logger))
        self._add_step(GitIgnoreAdd(self._logger))
        self._add_step(InitializeRepoStructure(self._logger))
        self._add_step(AddSubmodules(self._logger))

        if self._multi_language:
            self._add_step(CopyRouterBinary(self._logger, self._configuration))
            self._add_step(AddLaunchScript(self._logger))
