#include <stdio.h>
#include "${PROJECT_NAME}/${PROJECT_NAME}.h"

/* Simple example API impl */
int ${PROJECT_NAME}_add(int a, int b) {
    return a + b;
}

const char* ${PROJECT_NAME}_version_string(void) {
    /* Keep this tiny and compile-time only */
    return "${PROJECT_VERSION}";
}
