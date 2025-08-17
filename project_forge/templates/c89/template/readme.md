# ${PROJECT_NAME}

Small C library.

## Build

```bash
cmake -S . -B build -D${PROJECT_NAME}_BUILD_APP=ON -D${PROJECT_NAME}_BUILD_TESTS=ON
cmake --build build
ctest --test-dir build
```
