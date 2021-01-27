#include "stdint.h"

// Test include directories added from supplied memory_statistics config.
// This header is in ./include which is in the config for testing the
// memory_statistics action.
#include "test_header.h"

// Test compiler flags added from supplied memory_statistics config.
// TEST_FLAG is in the compiler_flags array of the config for testing the
// memory_statistics action.
#ifdef TEST_FLAG

// This should add 10340 bytes to the .text section.
// The result should be memory_statistics reporting 10.1K for this file.
const uint8_t array[10340] = {1};
#endif
