# Created by LordMartron94 on 18/08/2025.
import re
from typing import Dict

from project_forge.common.py_common.logging import HoornLogger


def replace_variables(input_string: str, keyword_mapping: Dict[str, str], logger: HoornLogger) -> str:
    """
    Replaces known variables in a string and warns about unsupported ones.
    """
    # Find all potential variables
    potential_vars = re.findall(r"\$\{.*?}", input_string)
    for var in potential_vars:
        if var not in keyword_mapping:
            logger.warning(f"Unsupported variable found: '{var}'", separator="APP")

    # Replace known variables
    for key, value in keyword_mapping.items():
        input_string = input_string.replace(key, value)
    return input_string
