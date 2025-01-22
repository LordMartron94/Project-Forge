import json
from pathlib import Path
from typing import Dict, List

from project_forge.common.py_common.logging import HoornLogger
from project_forge.common.py_common.patterns import IPipe
from project_forge.common.py_common.user_input.user_input_helper import UserInputHelper
from project_forge.pipeline.pipeline_context import PipelineContext


class InitializeFrameworks(IPipe):
    # TODO - Refactor & CLEAN

    def __init__(self, logger: HoornLogger, user_input_handler: UserInputHelper):
        self._logger = logger
        self._user_input_handler = user_input_handler

    def flow(self, data: PipelineContext) -> PipelineContext:
        self._logger.trace("Flowing pipe for framework add.")

        keyword_mapping: Dict[str, str] = {
            "${SANITIZED_NAME}": data.project_root_name_sanitized,
            "${ROOT_FOLDER_NAME}": data.project_root_name,
            "${GIT_URL}": data.git_url
        }

        copy_to_root: List[Path] = []

        for template in data.included_templates:
            framework_path = template.joinpath("frameworks.json")

            if not framework_path.exists(): continue

            options: List[Dict] = []
            with open(framework_path, "r") as f:
                frameworks = json.load(f)
                for framework in frameworks:
                    options.append(framework)

            chosen_options = self._get_desired_frameworks_from_user(options)
            copy_to_root.extend(template.joinpath(option["copy_to_root"]) for option in chosen_options)

        for copy_to_root_file in copy_to_root:
            if copy_to_root_file.name.endswith(".json"):
                with open(copy_to_root_file, "r") as f:
                    old_content: str = f.read()
                    new_content: str = old_content

                    for key, value in keyword_mapping.items():
                        new_content = new_content.replace(key, value)

                    with open(data.repo_path.joinpath(copy_to_root_file.name), "w") as f2:
                        f2.write(new_content)

        self._logger.trace("Done flowing pipe for framework add.")

        return data

    def _get_desired_frameworks_from_user(self, frameworks: List[Dict]) -> List[Dict]:
        def __validate_input(input_value: str) -> [bool, str]:
            choices: List[int] = [int(num) for num in input_value.split()]

            valid: bool = all(1 <= choice <= len(frameworks) for choice in choices)

            if not valid:
                return False, "Please enter a number between 1 and " + str(len(frameworks)) + " separated by spaces."

            return True, ""

        for i, framework in enumerate(frameworks):
            print(f"{i+1}) {framework['name']}")

        choice = self._user_input_handler.get_user_input("Enter the numbers of the frameworks you want to include (separated by spaces):", expected_response_type=str, validator_func=__validate_input)
        return [frameworks[choice-1] for choice in [int(num) for num in choice.split()]]
