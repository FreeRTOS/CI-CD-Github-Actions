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

    logging.info("START OF EXECUTABLE OUTPUT\n")

    # While a timeout hasn't happened, the executable is running, and an exit condition has not been met
    while ( not exit_condition_met ):
        # Check if executable exitted
        exe_exit_status = exe.poll()
        if (exe_exit_status is not None) and (exe_exitted is False):
            logging.info(f"EXECUTABLE CLOSED WITH STATUS: {exe_exit_status}")
            exe_exitted = True
            exit_condition_met = True

        exe_stdout_line = exe.stdout.readline()
        if(exe_stdout_line is not None) and (len(exe_stdout_line.strip()) > 1):
            # Check if the executable printed out its success line
            if ( args.success_line is not None ) and ( args.success_line in exe_stdout_line ) :
                logging.info(f"SUCCESS_LINE_FOUND: {exe_stdout_line}")
                # Mark that we found the success line, kill the executable
                success_line_found = True
                exit_condition_met = True
                exe.kill()
                time.sleep(.05)
            else:
                logging.info(exe_stdout_line)

        # Check for timeout
        cur_time_seconds = time.time()
        if cur_time_seconds >= timeout_time_seconds:
            logging.info(f"TIMEOUT OF {args.timeout_seconds} SECONDS HIT")
            exit_condition_met = True
        
        # Sleep for a short duration between loops to not steal all system resources
        # time.sleep(.05)

    if not exe_exitted and not success_line_found:
        logging.info(f"EXECUTABLE DID NOT EXIT, MANUALLY KILLING NOW")
        exe.kill()
        logging.info(f"PARSING REST OF LOG")
        # Capture remaining output and check for the successful line
        for exe_stdout_line in exe.stdout.readlines():
            logging.info(exe_stdout_line)
            if args.success_line is not None and args.success_line in exe_stdout_line:
                success_line_found = True
                logging.info(f"SUCCESS_LINE_FOUND: {exe_stdout_line}")

    logging.info("END OF DEVICE OUTPUT")
    logging.info("EXECUTABLE RUN SUMMARY:")

    exit_status = 1
    # Check if a success line was found if that is an option
    if ( args.success_line is not None) and (not success_line_found ):
        logging.error("Success Line: Success line not output.")
        exit_status = 1
    elif( args.success_line is not None) and ( success_line_found ):
        exit_status = 0
        logging.info(f"Success Line: Success line was output")
    
    # Check if a exit status was found if that was an option
    if ( ( exit_status != 0 ) and ( args.success_exit_status is not None) ):
        # If the executable had to be force killed mark it as a failure
        if( not exe_exitted):
            logging.error("Exit Status: Executable did not exit by itself.\n")
            exit_status = 1
        # If the executable exited with a different status mark it as a failure
        elif ( ( exe_exitted ) and ( exe_exit_status != args.success_exit_status ) ):
            logging.error(f"Exit Status: {exe_exit_status} is not equal to requested exit status of {args.success_exit_status}\n")    
            exit_status = 1
        # If the executable exited with the same status as requested mark a success
        elif ( ( exe_exitted ) and ( exe_exit_status == args.success_exit_status ) ):
            logging.info(f"Exit Status: Executable exited with requested exit status")
            exit_status = 0

    logging.info(f"Runner thread exiting with status {exit_status}\n")
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

    elif args.success_exit_status is not None and args.success_line is not None:
        logging.warning("Received an option for success-line and success-exit-status.")
        logging.warning("Be aware: This program will report SUCCESS on either of these conditions being met")

    if not os.path.exists(args.exe_path):
        logging.error(f'Input executable path \"{args.exe_path}\" does not exist.')
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

    logging.info(f"Running executable: {exe_abs_path} ")
    logging.info(f"Storing logs in: {log_dir}")
    logging.info(f"Timeout (seconds) per run: {args.timeout_seconds}")
    
    if not args.retry_attempts:
        args.retry_attempts = 0
    else:
        logging.info(f"Will relaunch the executable {args.retry_attempts} times to look for a valid success metric")
    
    if args.success_line is not None:
        logging.info(f"Searching for success line: {args.success_line}")
    if args.success_exit_status is not None:
        logging.info(f"Searching for exit code: {args.success_exit_status}")
    
    # Small increase on the timeout to allow the thread to try and timeout
    threadTimeout = ( args.timeout_seconds + 3 )
    for attempts in range(0,args.retry_attempts + 1):
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
            logging.warning(f"EXECUTABLE HAS HIT TIMEOUT OF {threadTimeout - 3} SECONDS: FORCE KILLING THREAD")
            thread.kill()
            exit_status = 1
        else:
            exit_status = thread.exitcode
            logging.info(f"THREAD EXITED WITH EXITCODE {exit_status}")

        if( ( attempts  < args.retry_attempts ) and exit_status == 1 ):
            logging.warning(f"DID NOT RECEIVE SUCCESSFUL EXIT STATUS, TRYING RE-ATTEMPT {attempts+1} OF {args.retry_attempts}\n")
        else:
            break

    logging.info(f"EXECUTABLE MONITOR EXITING WITH STATUS: {exit_status}")
    # Report final exit status if no successful run occured
    sys.exit(exit_status)
