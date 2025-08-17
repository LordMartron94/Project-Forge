#include <stdio.h>
#include "${PROJECT_NAME}/${PROJECT_NAME}.h"

int main(void) {
    printf("[${PROJECT_NAME}] Hello from demo app!\n");
    printf("[${PROJECT_NAME}] add(2, 3) = %d\n", ${PROJECT_NAME}_add(2, 3));
    printf("[${PROJECT_NAME}] version = %s\n", ${PROJECT_NAME}_version_string());
    return 0;
}
