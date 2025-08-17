#ifndef ${PROJECT_NAME_UPPER}_${PROJECT_NAME_UPPER}_H
#define ${PROJECT_NAME_UPPER}_${PROJECT_NAME_UPPER}_H

#ifdef __cplusplus
extern "C" {
#endif

/* Version macros (optional) */
#ifndef ${PROJECT_NAME_UPPER}_VERSION_MAJOR
#define ${PROJECT_NAME_UPPER}_VERSION_MAJOR ${PROJECT_VERSION_MAJOR}
#endif
#ifndef ${PROJECT_NAME_UPPER}_VERSION_MINOR
#define ${PROJECT_NAME_UPPER}_VERSION_MINOR ${PROJECT_VERSION_MINOR}
#endif
#ifndef ${PROJECT_NAME_UPPER}_VERSION_PATCH
#define ${PROJECT_NAME_UPPER}_VERSION_PATCH ${PROJECT_VERSION_PATCH}
#endif

/* Public API */
int ${PROJECT_NAME}_add(int a, int b);
const char* ${PROJECT_NAME}_version_string(void);

#ifdef __cplusplus
}
#endif

#endif /* ${PROJECT_NAME_UPPER}_${PROJECT_NAME_UPPER}_H */
