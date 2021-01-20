# CI-CD-GitHub-Actions

This repository contains common GitHub Actions for use in CI/CD on FreeRTOS library repositories.

Currently, this repository contains actions for the following code quality checks that are run on
FreeRTOS libraries.

* **Complexity** - Uses [GNU Complexity](https://www.gnu.org/software/complexity/manual/complexity.html)
  to verify that the complexity score of library functions is less than 9.
* **Formatting** - Validates all C files of a FreeRTOS library repository comply to the formatting
  standard defined in [uncrustify.cfg](formatting/uncrustify.cfg).
* **Doxygen** - Validates that the doxygen manual of the FreeRTOS library can be built without
  warnings.
* **Spellings** - Checks spellings across all files of the FreeRTOS library repository. Each
  FreeRTOS library repository should have a **lexicon.txt** file.
* **Coverage Cop** - Enforces that the unit tests of a FreeRTOS library meet the minimum thresholds
  branch and line coverages. The **lcov** coverage output from running unit tests should be
  available before using this action.
* **Memory Statistics** - Generates the library size tables used in FreeRTOS library
  documentation.
