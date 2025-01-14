from pathlib import Path
from typing import List

from pydantic import BaseModel


class PipelineContext(BaseModel):
    project_path: Path
    root_project_path: Path
    included_templates: List[Path]
    project_root_name: str
    submodule_root_name: str
    multi_language: bool
