cmake_minimum_required(VERSION 3.28)

project(${PROJECT_NAME}
  VERSION ${PROJECT_VERSION}
  DESCRIPTION "C library: ${PROJECT_NAME}"
  LANGUAGES C
)

set(CMAKE_C_STANDARD 90)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

option(${PROJECT_NAME}_BUILD_APP   "Build demo console app (src/main.c)" ON)
option(${PROJECT_NAME}_BUILD_TESTS "Build tests in /tests"               ON)
option(BUILD_SHARED_LIBS           "Build shared instead of static"      OFF)

include(GNUInstallDirs)

# -------------------- Dependencies (discovery + selection) --------------------
# Choose how this library obtains its dependencies.
option(${PROJECT_NAME}_USE_BUNDLED_SUBMODULES "Use submodules from external/*" ON)

# --- Cache definitions that Projects depend on ---
# set(NEXUS_DOUBLE_PRECISION ON CACHE BOOL "" FORCE)

# Accumulate deps here; apply them after add_library()
set(${PROJECT_NAME}_PUBLIC_DEPS  "")  # e.g. nexus::nexus
set(${PROJECT_NAME}_PRIVATE_DEPS "")  # e.g. chaos::chaos

if(${PROJECT_NAME}_USE_BUNDLED_SUBMODULES)
  # Example: disable submodule demos/tests
  # set(nexus_BUILD_APP   OFF CACHE BOOL "" FORCE)
  # set(nexus_BUILD_TESTS OFF CACHE BOOL "" FORCE)
  # set(chaos_BUILD_APP   OFF CACHE BOOL "" FORCE)
  # set(chaos_BUILD_TESTS OFF CACHE BOOL "" FORCE)

  # Bring sources into this build (order matters if they depend on each other)
  # add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/external/nexus)
  # add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/external/chaos)
else()
  # Use installed packages (or targets provided by a parent project)
  # if(NOT TARGET nexus::nexus)
  #   find_package(nexus CONFIG REQUIRED) # optionally: find_package(nexus 1.2 CONFIG REQUIRED)
  # endif()
  # if(NOT TARGET chaos::chaos)
  #   find_package(chaos CONFIG REQUIRED)
  # endif()
endif()

# Decide visibility (examples):
# list(APPEND ${PROJECT_NAME}_PUBLIC_DEPS  nexus::nexus)  # appears in public headers
# list(APPEND ${PROJECT_NAME}_PRIVATE_DEPS chaos::chaos)  # used only in .c files

# ------------------------------------------------------------------------------

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

# ---- Apply dependency link interfaces (MUST be after add_library) ----
# Safe even if the lists are empty.
target_link_libraries(${PROJECT_NAME}
  PUBLIC  ${${PROJECT_NAME}_PUBLIC_DEPS}
  PRIVATE ${${PROJECT_NAME}_PRIVATE_DEPS}
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

# Build-tree export for add_subdirectory() consumers
export(EXPORT ${PROJECT_NAME}Targets
  NAMESPACE ${PROJECT_NAME}::
  FILE ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Targets.cmake
)
