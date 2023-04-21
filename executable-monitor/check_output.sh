#!/bin/bash

OUTPUT_FILE="$1"
EXPECTED_STRING="$2"

# Check if expected string is in output file
if grep -q "$EXPECTED_STRING" "$OUTPUT_FILE"; then
    echo -e "\nSUCCESS - Found SUCCESS string in output."
else
    echo -e "\nFAILURE - SUCCESS string not found in output."
    exit 1
fi
