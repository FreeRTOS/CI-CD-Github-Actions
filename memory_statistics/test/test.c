#include "stdint.h"

// Test include directories added from memory_statistics config.
// This header is in ./include which is in the test config's includes.
#include "test_header.h"

// Test compiler flags added from memory_statististics config.
// TEST_FLAG is set in the test config's compiler_flags array.
#ifdef TEST_FLAG

// This should add 10340 bytes to the .text section.
// The result should be memory_statistics reporting 10.1K for this file.
const uint8_t array[10340] = {1};
#endif
