from pathlib import Path

from project_forge.common.py_common.logging import HoornLogger
from project_forge.common.py_common.patterns import IPipe
from project_forge.pipeline.pipeline_context import PipelineContext


class AddLaunchScript(IPipe):
    def __init__(self, logger: HoornLogger):
        self._logger = logger

    def flow(self, data: PipelineContext) -> PipelineContext:
        self._logger.trace("Adding launch script")
        launch_script_path: Path = data.project_path.joinpath("launch.ps1")
        with open(launch_script_path, "w") as launch_script:
            launch_script.write(f"""./venv/Scripts/activate.ps1
    
    # Get the current working directory
    $originalDir = Get-Location
    $newDir = Join-Path -Path $originalDir -ChildPath "{data.project_root_name}" -AdditionalChildPath ("components", "MD.Launcher")
    
    # Add the project's root directory to PYTHONPATH
    $env:PYTHONPATH = "$newDir" + ";" + $env:PYTHONPATH
    
    py "./{data.project_path.joinpath(data.project_root_name, "components", "MD.Launcher", "md_launcher", "components", "launcher", "launch.py").relative_to(data.project_path)}" "./launch_config.json"
    """)

        self._logger.trace("Launch script added successfully")
        return data