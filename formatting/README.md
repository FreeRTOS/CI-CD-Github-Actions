# Uncrustify Format GitHub Action
## Purpose
This directory contains an [action.yml](action.yml) file to uncrustify code
files inside of [FreeRTOS](https://github.com/FreeRTOS/) repositories. It
additionally will check for files with trailing whitespace, and CRLF line
endings.

If a file is found that contains incorrect formatting, trailing whitespace, or
CRLF endings, this action will create a Git Patch that will be added to the
summary of the workflow run that uses this action. This allows an end user to
download the patch, apply it, and then pass the formatting checks.

A patch is provided, instead of automatically applying the updates, as
automatically formatting files could lead to merge conflicts. If an end-user
didn't know they need to perform a `git pull` as their origin would have the
formatting change applied.

## Testing Files
This directory contains many files that are used to test the action.
These tests can be found inside of
[formattingTests.yml](../.github/workflows/formattingTests.yml).
The files have been named in such a way to explain what their purpose is.
The general idea is that there are a mix of files, some with CRLF endings,
some with uncrustify errors, and some with trailing whitespace. Where the
inside of
[formattingTests.yml](../.github/workflows/formattingTests.yml)
these various files are checked to ensure this action properly fails when
a formatting issue is discovered. Additional tests are here to ensure that
the various input parameters to the action work as intended.
