Test the case where exit status code and success line are given but hit timeout
python3 executable-monitor.py --log-dir . --success-exit-status 0 --success-line "Sleeping for 27 seconds"  --retry-attempts 2 --timeout-seconds 10 --exe-path test.out ; echo $?

# Run a test where we find the success line but the exe does not exit, ensure exit status is 0
#python3 executable-monitor.py --log-dir . --success-line "Sleeping for 27 seconds"  --retry-attempts 2 --timeout-seconds 10 --exe-path test.out; echo $?

Test a run where the thread will timeout while waiting for the success message, ensure exit status is 1
# python3 executable-monitor.py --log-dir . --success-line "Sleeping for 27 seconds"  --retry-attempts 2 --timeout-seconds 2 --exe-path test.out; echo $?