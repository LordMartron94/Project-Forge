from pathlib import Path

import pydantic


class ConfigModel(pydantic.BaseModel):
	project_dir: Path
	venv_dir: Path
	latest_router_exe: Path
