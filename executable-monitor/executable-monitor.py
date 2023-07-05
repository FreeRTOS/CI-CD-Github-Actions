#!/usr/bin/env python3

import os, sys
from argparse import ArgumentParser
import subprocess
import time
import logging


if __name__ == '__main__':

    # Set up logging
    logging.getLogger().setLevel(logging.NOTSET)

    # Add stdout handler to logging
    stdout_logging_handler = logging.StreamHandler(sys.stdout)
    stdout_logging_handler.setLevel(logging.DEBUG)
    stdout_logging_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stdout_logging_handler.setFormatter(stdout_logging_formatter)
    logging.getLogger().addHandler(stdout_logging_handler)

    # Parse arguments
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
    parser.add_argument('--success-line',
                        type=str,
                        required=False,
                        help='Line that indicates executable completed successfully. Required if --success-exit-status is not used.')
    parser.add_argument('--success-exit-status',
                        type=int,
                        required=False,
                        help='Exit status that indicates that the executable completed successfully. Required if --success-line is not used.')

    args = parser.parse_args()

    if args.success_exit_status is None and args.success_line is None:
        logging.error("Must specify at least one of the following: --success-line, --success-exit-status.")
        sys.exit(1)

    if not os.path.exists(args.exe_path):
        logging.error(f'Input executable path \"{args.exe_path}\" does not exist.')
        sys.exit(1)

    # Create log directory if it does not exist.
    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir, exist_ok = True)

    # Convert any relative path (like './') in passed argument to absolute path.
    exe_abs_path = os.path.abspath(args.exe_path)
    log_dir = os.path.abspath(args.log_dir)

    # Add file handler to output logging to a log file
    exe_name = os.path.basename(exe_abs_path)
    log_file_path = f'{log_dir}/{exe_name}_output.txt'
    file_logging_handler = logging.FileHandler(log_file_path)
    file_logging_handler.setLevel(logging.DEBUG)
    file_logging_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_logging_handler.setFormatter(file_logging_formatter)
    logging.getLogger().addHandler(file_logging_handler)

    logging.info(f"Running executable: {exe_abs_path} ")
    logging.info(f"Storing logs in: {log_dir}")
    logging.info(f"Timeout (seconds): {args.timeout_seconds}")

    # Initialize values
    timeout_occurred = False
    exe_exit_status = None
    exe_exitted = False
    success_line_found = False
    wait_for_exit = args.success_exit_status is not None

    # Launch the executable
    exe = subprocess.Popen([exe_abs_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

    cur_time_seconds = time.time()
    timeout_time_seconds = cur_time_seconds + args.timeout_seconds

    logging.info("START OF DEVICE OUTPUT\n")

    while not (timeout_occurred or exe_exitted or (not wait_for_exit and success_line_found)):

        # Check if executable exitted
        exe_exit_status = exe.poll()
        if exe_exit_status is not None:
            exe_exitted = True

        # Read executable's stdout and write to stdout and logfile
        exe_stdout_line = exe.stdout.readline()
        logging.info(exe_stdout_line)

        # Check if the executable printed out it's success line
        if args.success_line is not None and args.success_line in exe_stdout_line:
            success_line_found = True

        # Check for timeout
        cur_time_seconds = time.time()
        if cur_time_seconds >= timeout_time_seconds:
            timeout_occurred = True

        # Sleep for a short duration between loops to not steal all system resources
        time.sleep(.1)

    if not exe_exitted:
        exe.kill()

    # Capture remaining output and check for the successful line
    for exe_stdout_line in exe.stdout.readlines():
        logging.info(exe_stdout_line)
        if args.success_line is not None and args.success_line in exe_stdout_line:
            success_line_found = True
    
    logging.info("END OF DEVICE OUTPUT\n")

    logging.info("EXECUTABLE RUN SUMMARY:\n")

    exit_status = 0

    if args.success_line is not None:
        if success_line_found:
            logging.info("Success Line: Found.\n")
        else:
            logging.error("Success Line: Success line not output.\n")
            exit_status = 1

    if args.success_exit_status is not None:
        if exe_exitted:
            if exe_exit_status != args.success_exit_status:
                exit_status = 1
            logging.info(f"Exit Status: {exe_exit_status}")
        else:
            logging.error("Exit Status: Executable did not exit.\n")
            exe_status = 1
    

    # Report if executable executed successfully to workflow
    sys.exit(exit_status)
