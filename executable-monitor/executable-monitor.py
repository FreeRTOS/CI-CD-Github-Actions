#!/usr/bin/env python3

import os, sys
from argparse import ArgumentParser
import subprocess
import time
import logging
from multiprocessing import Process

def runAndMonitor(args):
    # Set up logging
    logging.getLogger().setLevel(logging.NOTSET)

    # Add stdout handler to logging
    stdout_logging_handler = logging.StreamHandler(sys.stdout)
    stdout_logging_handler.setLevel(logging.DEBUG)
    stdout_logging_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stdout_logging_handler.setFormatter(stdout_logging_formatter)
    logging.getLogger().addHandler(stdout_logging_handler)

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

    if args.success_exit_status is not None:
        logging.info("Looking for exit status {0}".format(args.success_exit_status ))

    # Initialize values
    exe_exit_status = None
    exe_exitted = False
    success_line_found = False
    exit_condition_met = False
    wait_for_exit = args.success_exit_status is not None

    # Launch the executable
    exe = subprocess.Popen([exe_abs_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, env=os.environ)

    cur_time_seconds = time.time()
    timeout_time_seconds = cur_time_seconds + args.timeout_seconds

    logging.info("START OF DEVICE OUTPUT\n")

    # While a timeout hasn't happened, the executable is running, and an exit condition has not been met
    while ( not exit_condition_met ):
        # Check if executable exitted
        exe_exit_status = exe.poll()
        if (exe_exit_status is not None) and (exe_exitted is False):
            logging.info(f"EXECUTABLE CLOSED WITH STATUS: {exe_exit_status}")
            exe_exitted = True
            if( args.success_line is None):
                exit_condition_met = True

        exe_stdout_line = exe.stdout.readline()
        if(exe_stdout_line is not None) and (len(exe_stdout_line.strip()) > 1):
            # Check if the executable printed out its success line
            if ( args.success_line is not None ) and ( args.success_line in exe_stdout_line ) :
                logging.info(f"SUCCESS_LINE_FOUND: {exe_stdout_line}")
                success_line_found = True
                if( not wait_for_exit ):
                    exit_condition_met = True
                    exe.kill()
            else:
                logging.info(exe_stdout_line)

        # Check for timeout
        cur_time_seconds = time.time()
        if cur_time_seconds >= timeout_time_seconds:
            logging.info(f"TIMEOUT OF {args.timeout_seconds} SECONDS HIT")
            exit_condition_met = True
        
        # Sleep for a short duration between loops to not steal all system resources
        # time.sleep(.05)

    if not exe_exitted:
        logging.info(f"EXECUTABLE DID NOT EXIT, MANUALLY KILLING NOW")
        exe.kill()

    if not exit_condition_met:
        logging.info(f"PARSING REST OF LOG")
        # Capture remaining output and check for the successful line
        for exe_stdout_line in exe.stdout.readlines():
            logging.info(exe_stdout_line)
            if args.success_line is not None and args.success_line in exe_stdout_line:
                success_line_found = True
                logging.info(f"SUCCESS_LINE_FOUND: {exe_stdout_line}")

    logging.info("END OF DEVICE OUTPUT")
    logging.info("EXECUTABLE RUN SUMMARY:")
    exit_status = 0

    if args.success_line is not None:
        if not success_line_found:
            logging.error("Success Line: Success line not output.\n")
            exit_status = 1

    if args.success_exit_status is not None:
        if exe_exitted:
            if exe_exit_status != args.success_exit_status:
                exit_status = 1
            logging.info(f"Exit Status: {exe_exit_status}\n")
        else:
            logging.error("Exit Status: Executable did not exit by itself.\n")
            exit_status = 1

    if( exit_status == 0 ):
        logging.info(f"Run found a valid success metric\n")
    
    else:
        logging.error("Run did not find a valid success metric.\n")
    
    logging.info(f"Runner thread exiiting with status {exit_status}")
    exit(exit_status)

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
                        type=str,
                        required=False,
                        help='Exit status that indicates that the executable completed successfully. Required if --success-line is not used.')
    parser.add_argument('--retry-attempts',
                        type=int,
                        required=False,
                        help='Number of times to attempt re-running the executable if the correct exit condition is not found.')

    args = parser.parse_args()

    # GitHub action needs to be able to pass in a "blank" value. This means the parser needs to take in success exit status as a str
    # Check if it was the blank value, if it was set it to None. If it was not convert it to an integer
    if args.success_exit_status == "":
        args.success_exit_status = None
    else:
        args.success_exit_status = int(args.success_exit_status)

    if args.success_exit_status is None and args.success_line is None:
        logging.info("Must specify at least one of the following: --success-line, --success-exit-status.")
        sys.exit(1)

    if not os.path.exists(args.exe_path):
        logging.info(f'Input executable path \"{args.exe_path}\" does not exist.')
        sys.exit(1)

    # Convert any relative path (like './') in passed argument to absolute path.
    exe_abs_path = os.path.abspath(args.exe_path)
    log_dir = os.path.abspath(args.log_dir)

    # Create log directory if it does not exist.
    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir, exist_ok = True)

    # Add file handler to output logging to a log file
    exe_name = os.path.basename(exe_abs_path)
    log_file_path = f'{log_dir}/{exe_name}_output.txt'
    file_logging_handler = logging.FileHandler(log_file_path)
    file_logging_handler.setLevel(logging.DEBUG)
    file_logging_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_logging_handler.setFormatter(file_logging_formatter)
    logging.getLogger().addHandler(file_logging_handler)

    if not args.retry_attempts:
        retryAttempts = 0
    else:
        retryAttempts = args.retry_attempts
    
    logging.info(f"Running executable: {exe_abs_path} ")
    logging.info(f"Storing logs in: {log_dir}")
    logging.info(f"Timeout (seconds) per run: {args.timeout_seconds}")
    logging.info(f"Searching for success line: {args.success_line}\n")

    # Small increase on the timeout to allow the thread to try and timeout
    threadTimeout = ( args.timeout_seconds + 3 )
    for attempts in range(0,retryAttempts + 1):
        exit_status = 1
        # Set the timeout for the thread    
        thread = Process(target=runAndMonitor, args=(args,))
        thread.start()
        # Wait for the thread to join, or hit a timeout. 
        thread.join(timeout=threadTimeout)
        # As join() always returns None, you must call is_alive() after join() to decide whether a timeout happened
        # If the thread is still alive, the join() call timed out.       
        if ( ( thread.exitcode is None ) and ( thread.is_alive() ) ):
            # Print the thread timeout they passed in to the log
            logging.info(f"EXECUTABLE HAS HIT TIMEOUT OF {threadTimeout - 1} SECONDS: FORCE KILLING THREAD")
            thread.kill()
            exit_status = 1
        else:
            exit_status = thread.exitcode
            logging.info(f"THREAD EXITED WITH EXITCODE {exit_status}")

        if( ( attempts < retryAttempts ) and exit_status == 1 ):
            logging.info(f"DID NOT RECEIVE SUCCESSFUL EXIT STATUS, TRYING RE-ATTEMPT {attempts+1} OF {retryAttempts}\n")
        else:
            break

    logging.info(f"EXECUTABLE MONITOR EXITING WITH STATUS: {exit_status}")
    # Report final exit status if no successful run occured
    sys.exit(exit_status)
