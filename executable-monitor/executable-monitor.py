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

    #exe = subprocess.Popen([exe_abs_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    logging.info("START OF DEVICE OUTPUT\n")
    success_line_found = False

    try:
        exe = subprocess.run( 
            [exe_abs_path], 
            capture_output=True,
            timeout=args.timeout_seconds,
            text=True,
            encoding="utf-8")
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        logging.info(e.stdout.decode())
        logging.warning(" Abnormal exit \n")
        with open(log_file_path) as of:
            for exe_stdout_line in of.readlines():
                if args.success_line is not None and args.success_line in exe_stdout_line:
                    success_line_found = True


    else: 
        logging.info(exe.stdout)
        with open(log_file_path) as of:
            for exe_stdout_line in of.readlines():
                if args.success_line is not None and args.success_line in exe_stdout_line:
                    success_line_found = True
    
    logging.info("END OF DEVICE OUTPUT\n")

    logging.info("EXECUTABLE RUN SUMMARY:\n")

    exit_status = 0

    if args.success_line is not None:
        if success_line_found:
            logging.info("Success Line: Found.\n")
        else:
            logging.error("Success Line: Not found.\n")
            exit_status = 1

    sys.exit(exit_status)
