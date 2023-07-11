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
    parser.add_argument('--retry-attempts',
                        type=int,
                        required=False,
                        help='Number of times to attempt re-running the executable if the correct exit condition is not found.')

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

    if not args.retry_attempts:
        retryAttempts = 0
    else:
        retryAttempts = args.retry_attempts

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
    logging.info(f"Searching for success line: {args.success_line}")
    logging.info(f"Will re-try the run {retryAttempts} times")
    if args.success_exit_status is not None:
        logging.info("Looking for exit status {0}".format(args.success_exit_status ))
    for attempts in range(0,retryAttempts + 1):

        # Initialize values
        success_line = ""
        timeout_occurred = False
        exe_exit_status = None
        exe_exitted = False
        success_line_found = False
        exit_condition_met = False
        wait_for_exit = args.success_exit_status is not None

        # Create two file descriptors. The subprocess writes to one, the parent task reads from the other
        # This is a workaround to avoid the fact that calling readline() on the stdout of the subprocess is
        # a blocking call. Where if the subprocess is running but hasn't printed anything, readline will never time out.
        # The approach uses the underlying file system to not block on data that hasn't been written.
        WriteOutputFile = open("output.log", "w")
        ReadOutputFile = open("output.log", "r")

        # Launch the executable
        exe = subprocess.Popen([exe_abs_path], stdout=WriteOutputFile, stderr=WriteOutputFile, universal_newlines=True)

        cur_time_seconds = time.time()
        timeout_time_seconds = cur_time_seconds + args.timeout_seconds

        logging.info("START OF DEVICE OUTPUT\n")

        # While a timeout hasn't happened, the executable is running, and an exit condition has not been met
        while ( not exit_condition_met ):
            # Uncomment this sleep for a short duration between loops to not steal all system resources
            # time.sleep(.05)

            # Check if executable exitted
            exe_exit_status = exe.poll()
            if exe_exit_status is not None:
                logging.info(f"EXECUTABLE CLOSED WITH STATUS: {exe_exit_status}")
                exe_exitted = True
                exit_condition_met = True

            # Read executable's stdout and write to stdout and logfile
            # A potential improvement here would be to do readlines() on the file, then truncate()
            # This might be cleaner than this approach of reading a single line each loop.
            exe_stdout_line = ReadOutputFile.readline()
            if(exe_stdout_line is not None) and (len(exe_stdout_line.strip()) > 1):
                # Check if the executable printed out its success line
                if ( args.success_line is not None ) and ( args.success_line in exe_stdout_line ) :
                    logging.info(f"SUCCESS_LINE_FOUND: {exe_stdout_line}")
                    success_line_found = True
                    success_line = exe_stdout_line
                    if( not wait_for_exit ):
                        exit_condition_met = True
                else:
                    logging.info(exe_stdout_line)

            # Check for timeout
            cur_time_seconds = time.time()
            if cur_time_seconds >= timeout_time_seconds:
                logging.info(f"TIMEOUT OF {args.timeout_seconds} SECONDS HIT")
                timeout_occurred = True
                exit_condition_met = True

        if not exe_exitted:
            logging.info(f"EXECUTABLE DID NOT EXIT, MANUALLY KILLING NOW")
            exe.kill()

        if not exit_condition_met:
            logging.info(f"PARSING REST OF LOG")
            # Capture remaining output and check for the successful line
            for exe_stdout_line in ReadOutputFile.readlines():
                logging.info(exe_stdout_line)
                if args.success_line is not None and args.success_line in exe_stdout_line:
                    success_line_found = True
                    success_line = exe_stdout_line
                    logging.info(f"SUCCESS_LINE_FOUND: {exe_stdout_line}")

        # Close the files
        WriteOutputFile.close()
        ReadOutputFile.close()

        logging.info("END OF DEVICE OUTPUT")

        logging.info("EXECUTABLE RUN SUMMARY:\n")

        exit_status = 0

        if args.success_line is not None:
            if not success_line_found:
                logging.error("Success Line: Success line not output.\n")
                exit_status = 1

        if args.success_exit_status is not None:
            if exe_exitted:
                if exe_exit_status != args.success_exit_status:
                    exit_status = 1
                logging.info(f"Exit Status: {exe_exit_status}")
            else:
                logging.error("Exit Status: Executable did not exit by itself.\n")
                exit_status = 1

        if( exit_status == 0 ):
            logging.info(f"Run found a valid success metric\n")
            sys.exit(exit_status)

        elif( attempts < retryAttempts ):
            logging.info(f"Did not succeed, trying re-attempt {attempts+1} of {retryAttempts}\n")

    # Report final exit status if no successful run occured
    sys.exit(exit_status)
