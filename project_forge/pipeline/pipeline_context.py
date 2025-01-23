from pathlib import Path
from typing import List, Dict

from pydantic import BaseModel


class PipelineContext(BaseModel):
    repo_path: Path
    project_path: Path
    included_templates: List[Path]
    project_root_name: str
    project_root_name_sanitized: str
    submodule_root_name: str
    multi_language: bool
    git_url: str
    extra_submodules: List[Dict] = []
