# Executable Monitor Summary:
This is a python program designed to run an executable and monitor it.
It can either look for a string being printed to the program's standard out, or check for an exit condition.
It supports retry logic, as well as deadlocking programs.
The tests for the executable monitor mostly live inside of the CI-CD-Github-Actions/.github/workflows/test.yml file.
A few tests have been added below for ease of copying and pasting it though.
These tests are meant to be run using the test.c file that lives inside of this directory.
test.c prints out the system time and then sleeps for a set duration
# Provided Test.c:
 test.c is a simple C program that prints the current minutes, hours, and seconds.
 As well as how long the program is going to sleep for.
 These values can then be used as a test for the executable-monitor.
```gcc test.c -o test.out```

Test.c can also be set to exit with the current time in minutes by using the command.
By setting the exit code or success line to be a time in the future a test can be written that requires retry logic.
By setting the success-line to be a time in the future the program will need to "retry" until this time occurs
By setting the exit code of the program to be the current minute, the program will need to "retry" until this exit code is seen.
```gcc test.c -DEXIT_WITH_MINUTES -o test.out```


# How to call the program locally with some basic tests.
 Success Test | Test the case where the success line is found but the exe does not exit, ensure exit status is 0
```python3 executable-monitor.py --success-line "SLEEPING FOR 6 SECONDS"  --retry-attempts 2 --timeout-seconds 10 --exe-path test.out; echo $?```

Success Test | Test the case where the success line is not found, but the exe exits, ensure exit status is 0
```python3 executable-monitor.py --success-line "THIS WILL NEVER PRINT" --success-exit-code 0 --retry-attempts 2 --timeout-seconds 60 --exe-path test.out; echo $?```

Failure Test | Test the case where exit status code and success line are given but hit timeout, ensure exit status is 1
```python3 executable-monitor.py --success-exit-code 0 --success-line "SLEEPING FOR 12 SECONDS"  --retry-attempts 2 --timeout-seconds 10 --exe-path test.out ; echo $?```
