### [CI-CD-Github-Actions](https://github.com/FreeRTOS/CI-CD-Github-Actions)

This repository contains common GitHub Actions for use in CI/CD
on [FreeRTOS](https://github.com/FreeRTOS/FreeRTOS-LTS/tree/main/FreeRTOS), and
[AWS](https://github.com/FreeRTOS/FreeRTOS-LTS/tree/main/aws), Library
Repositories.

This currently includes:

FreeRTOS Repositories:
 [FreeRTOS](https://github.com/FreeRTOS/FreeRTOS),
[FreeRTOS-Kernel](https://github.com/FreeRTOS/FreeRTOS-Kernel),
[FreeRTOS-Plus-TCP](https://github.com/FreeRTOS/FreeRTOS-Plus-TCP),
and [FreeRTOS-Cellular-Interface](https://github.com/FreeRTOS/FreeRTOS-Cellular-Interface),

FreeRTOS-Library Repositories:
 [backoffAlgorithm](https://github.com/FreeRTOS/backoffAlgorithm),
[coreHTTP](https://github.com/FreeRTOS/coreHTTP),
[coreJSON](https://github.com/FreeRTOS/coreJSON),
[coreMQTT](https://github.com/FreeRTOS/coreMQTT)
[corePKCS11](https://github.com/FreeRTOS/corePKCS11),
and [coreSNTP](https://github.com/FreeRTOS/coreSNTP),

AWS-Library Repositories:
 [Device-Defender](https://github.com/aws/device-defender-for-aws-iot-embedded-sdk),
[Device-Shadow](https://github.com/aws/device-shadow-for-aws-iot-embedded-sdk),
[Fleet-Provisioning](https://github.com/aws/fleet-provisioning-for-aws-iot-embedded-sdk),
[Jobs](https://github.com/aws/jobs-for-aws-iot-embedded-sdk),
[Ota](https://github.com/aws/ota-for-aws-iot-embedded-sdk),
and [Sigv4](https://github.com/aws/sigv4-for-aws-iot-embedded-sdk)


Currently, this repository contains actions for the following code quality
checks that are run on FreeRTOS libraries.

* **Complexity** - Uses
[GNU Complexity](https://www.gnu.org/software/complexity/manual/complexity.html)
to verify that the complexity score of library functions is less than 16.

* **Formatting** - Validates all C files of a FreeRTOS library repository comply to the
uncrustify formatting standard defined in [formatting](formatting/uncrustify.cfg).

* **Clang-Formatting** - Validates all C files of a FreeRTOS library repository comply to the formatting
  standard defined in [clang-format](formatting/.clang-format).

* **Doxygen** - Validates that the doxygen manual of the FreeRTOS library can be built without
  warnings.

* **Spellings** - Checks spellings across all files of the FreeRTOS library repository. Each
  FreeRTOS library repository should have a **.github/.cSpellWords.txt** file.

* **Coverage Cop** - Enforces that the unit tests of a FreeRTOS library meet the minimum thresholds
branch and line coverages. The **lcov** coverage output from running unit tests should be
available before using this action.

* **Memory Statistics** - Generates table of memory estimates for library
files used in FreeRTOS library documentation. The memory estimates are generated
by building the library with the ARM GCC toolchain.

* **Link Verifier** - Verifies links present in source and Markdown files.
Links verified include HTTP.

* **Manifest.yml Verifier** - Verifies that information of `manifest.yml` file
matches the state of a repository for the presence of submodules
and their commit IDs.

URLs, and - for Markdown files - relative file path links and section anchors.