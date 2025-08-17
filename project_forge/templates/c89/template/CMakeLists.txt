cmake_minimum_required(VERSION 3.28)

# --- Project meta (filled by your generator) ---
project(${PROJECT_NAME}
  VERSION ${PROJECT_VERSION}
  DESCRIPTION "C library: ${PROJECT_NAME}"
  LANGUAGES C
)

# C standard
set(CMAKE_C_STANDARD 90)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# Options
option(${PROJECT_NAME}_BUILD_APP   "Build demo console app (src/main.c)" ON)
option(${PROJECT_NAME}_BUILD_TESTS "Build tests in /tests"               ON)
option(BUILD_SHARED_LIBS           "Build shared instead of static"      OFF)

include(GNUInstallDirs)

# ---- Sources (recursively, exclude app entry from the lib) ----
file(GLOB_RECURSE ${PROJECT_NAME}_SOURCES CONFIGURE_DEPENDS
  "${CMAKE_CURRENT_SOURCE_DIR}/src/*.c"
)
list(FILTER ${PROJECT_NAME}_SOURCES EXCLUDE REGEX "/main\\.c$")

# ---- Library ----
add_library(${PROJECT_NAME} ${${PROJECT_NAME}_SOURCES})
add_library(${PROJECT_NAME}::${PROJECT_NAME} ALIAS ${PROJECT_NAME})

set_target_properties(${PROJECT_NAME} PROPERTIES
  POSITION_INDEPENDENT_CODE ON
  VERSION   ${PROJECT_VERSION}
  SOVERSION ${PROJECT_VERSION_MAJOR}
)

target_include_directories(${PROJECT_NAME}
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

# (Optional) warnings on MSVC/clang-cl
if (CMAKE_C_COMPILER_ID STREQUAL "Clang")
  target_compile_options(${PROJECT_NAME} PRIVATE /W4)
elseif (MSVC)
  target_compile_options(${PROJECT_NAME} PRIVATE /W4)
endif()

# ---- Demo app (optional) ----
if(${PROJECT_NAME}_BUILD_APP)
  add_executable(${PROJECT_NAME}_app src/main.c)
  target_link_libraries(${PROJECT_NAME}_app PRIVATE ${PROJECT_NAME}::${PROJECT_NAME})
endif()

# ---- Tests (optional & minimal) ----
if(${PROJECT_NAME}_BUILD_TESTS)
  enable_testing()
  add_executable(${PROJECT_NAME}_tests tests/entry.c)
  target_link_libraries(${PROJECT_NAME}_tests PRIVATE ${PROJECT_NAME}::${PROJECT_NAME})
  add_test(NAME ${PROJECT_NAME}.basic COMMAND ${PROJECT_NAME}_tests)
endif()

# ---- Install & export (find_package support) ----
include(CMakePackageConfigHelpers)

install(TARGETS ${PROJECT_NAME}
  EXPORT ${PROJECT_NAME}Targets
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

configure_package_config_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/cmake/${PROJECT_NAME}-config.cmake.in
  ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config.cmake
  INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}
)

write_basic_package_version_file(
  ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config-version.cmake
  VERSION ${PROJECT_VERSION}
  COMPATIBILITY SameMajorVersion
)

install(FILES
  ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config.cmake
  ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}-config-version.cmake
  DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}
)

install(EXPORT ${PROJECT_NAME}Targets
  NAMESPACE ${PROJECT_NAME}::
  DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}
)

export(EXPORT ${PROJECT_NAME}Targets
  NAMESPACE ${PROJECT_NAME}::
  FILE ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Targets.cmake
)
