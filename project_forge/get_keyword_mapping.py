# Created by LordMartron94 on 18/08/2025.
from typing import Dict

from project_forge.pipeline.pipeline_context import PipelineContext


def get_variable_mapping(data: PipelineContext) -> Dict[str, str]:
    version_parts = data.project_version.split('.')
    return {
        "${PROJECT_NAME}": data.project_root_name_sanitized,
        "${PROJECT_NAME_UPPER}": data.project_root_name_sanitized.upper(),
        "${SANITIZED_NAME}": data.project_root_name_sanitized,
        "${ROOT_FOLDER_NAME}": data.project_root_name,
        "${GIT_URL}": data.git_url,
        "${PROJECT_VERSION}": data.project_version,
        "${PROJECT_VERSION_MAJOR}": version_parts[0] if len(version_parts) > 0 else "0",
        "${PROJECT_VERSION_MINOR}": version_parts[1] if len(version_parts) > 1 else "0",
        "${PROJECT_VERSION_PATCH}": version_parts[2] if len(version_parts) > 2 else "0",
        "${CMAKE_CURRENT_SOURCE_DIR}": "${CMAKE_CURRENT_SOURCE_DIR}",
        "${CMAKE_CURRENT_BINARY_DIR}": "${CMAKE_CURRENT_BINARY_DIR}",
        "${CMAKE_CURRENT_LIST_DIR}": "${CMAKE_CURRENT_LIST_DIR}",
        "${CMAKE_INSTALL_INCLUDEDIR}": "${CMAKE_INSTALL_INCLUDEDIR}",
        "${CMAKE_INSTALL_LIBDIR}": "${CMAKE_INSTALL_LIBDIR}",
        "${CMAKE_INSTALL_BINDIR}": "${CMAKE_INSTALL_BINDIR}",
        "${sourceDir}": "${sourceDir}",
        "${presetName}": "${presetName}",
        "${LLVM_HOME}": "${LLVM_HOME}",
        "${${PROJECT_NAME}": "${${PROJECT_NAME}"
    }
