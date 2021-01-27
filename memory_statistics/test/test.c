#include "stdint.h"
// Test added include directories
#include "test_header.h"

// Test added compiler flags
#ifdef TEST_FLAG

// This should add 10340 bytes to .text
// The results should be memory_statistics reporting 10.1K for this file
const uint8_t array[10340] = {1};
#endif
