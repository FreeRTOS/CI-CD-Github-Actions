#!/usr/bin/env python3

import os, sys
from argparse import ArgumentParser
import subprocess
import time

if __name__ == '__main__':
    parser = ArgumentParser(description='Executable monitor.')
    parser.add_argument('--exe-path',
                        type=str,
                        required=True,
                        help='Path to the executable.')
    parser.add_argument('--log-dir',
                        type=str,
                        required=True,
                        help='Path to directory to store logs in.')
    parser.add_argument('--timeout-seconds',
                        type=int,
                        required=True,
                        help='Timeout for each executable run.')
    parser.add_argument('--number-of-runs',
                        type=int,
                        required=True,
                        help='Timeout for each executable run.')
    parser.add_argument('--success-line',
                        type=str,
                        required='--success-exit-status' not in sys.argv,
                        help='Line that indicates executable completed successfully. Required if --success-exit-status is not used.')
    parser.add_argument('--success-exit-status',
                        type=int,
                        required='--success-line' not in sys.argv,
                        help='Exit status that indicates that the executable completed successfully. Required if --success-line is not used.')

    args = parser.parse_args()

    if not os.path.exists(args.exe_path):
        print(f'Input executable path \"{args.exe_path}\" does not exist.')
        sys.exit(1)

    # Create log directory if it does not exist.
    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir, exist_ok = True)

    # Convert any relative path (like './') in passed argument to absolute path.
    EXE_PATH = os.path.abspath(args.exe_path)
    LOG_DIR = os.path.abspath(args.log_dir)

    print(f"Running executable: {EXE_PATH} ")
    print(f"Storing logs in: {LOG_DIR}")
    print(f"Timeout per run (seconds): {args.timeout_seconds}")
    print(f"Number of runs: {args.number_of_runs}")

    EXE_NAME = os.path.basename(EXE_PATH)

    log_file = open(f"{LOG_DIR}/{EXE_NAME}_output.txt', 'w')

    exe = subprocess.Popen([EXE_PATH], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
  
    cur_time_seconds = time.time()
    timeout_time_seconds = cur_time_seconds + args.timeout_seconds
    timeout_occurred = False

    exe_exit_status = None
    exe_exitted = False

    success_line_found = False
    cur_line_ouput = 1

    wait_for_exit = args.success_exit_status is not None       

    sys.stdout.write("DEVICE OUTPUT:\n\n")
    log_file.write("DEVICE OUTPUT:\n\n")

    while not (timeout_occurred or exe_exitted or (not wait_for_exit and success_line_found)):

        # Read executable's stdout and write to stdout and logfile
        exe_stdout_line = exe.stdout.readline()
        sys.stdout.write(exe_stdout_line)
        log_file.write(exe_stdout_line)

        # Check if the executable printed out it's success line
        if args.success_line in exe_stdout_line:
            success_line_found = True

        # Check if executable exitted
        exe_exit_status = exe.poll()
        if exe_exit_status is not None:
            exe_exitted = True

        # Check for timeout
        cur_time_seconds = time.time()
        if cur_time_seconds >= timeout_time_seconds:
            timeout_occurred = True

    if not exe_exitted:
        exe.kill()

    # Capture remaining output and check for the successful line
    for exe_stdout_line in exe.stdout.readlines()
        sys.stdout.write(exe_stdout_line)
        log_file.write(exe_stdout_line)
        if args.success_line in exe_stdout_line:
            success_line_found = True
    
    sys.stdout.write("\nEND OF DEVICE OUTPUT\n\n")
    log_file.write("\nEND_OF_DEVICE_OUTPUT:\n\n")

    sys.stdout.write("EXECUTABLE RUN SUMMARY:\n\n")
    log_file.write("EXECUTABLE RUN SUMMARY:\n\n")

    exit_status = 0

    if args.success_line is not None:
        if success_line_found:
            logfile.write("\nSuccess Line: Found.")
        else:
            logfile.write("\nSuccess Line: Success line not output.")
            exit_status = 1

    if args.success_exit_status is not None:
        if exe_exitted:
            if exe_exit_status != args.success_exit_status:
                exit_status = 1
            logfile.write(f"\nExit Status: {exe_exit_status}")
        else:
            logfile.write("\nExit Status: Executable did not exit.")
            exe_status = 1
    

    # Report if executable executed successfully to workflow
    sys.exit(exit_status)


