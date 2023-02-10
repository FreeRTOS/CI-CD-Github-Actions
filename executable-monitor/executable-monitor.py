#!/usr/bin/env python3

import os, sys
from argparse import ArgumentParser

if __name__ == '__main__':
    parser = ArgumentParser(description='manifest.yml verifier')
    parser.add_argument('--exe-path',
                        type=str,
                        required=True,
                        help='Path to the executable.')
    parser.add_argument('--timeout-seconds',
                        type=int,
                        required=True,
                        help='Timeout for each executable run.')
    parser.add_argument('--number-of-runs',
                        type=int,
                        required=True,
                        help='Timeout for each executable run.')

    args = parser.parse_args()

    if args.ignore_submodule_path != None:
        IGNORE_SUBMODULES_LIST = args.ignore_submodule_path.split(',')

    # Convert any relative path (like './') in passed argument to absolute path.
    EXE_PATH = os.path.abspath(args.exe_path)

    print(f"Running executable: {EXE_PATH} ")
    print(f"Timeout per run (seconds): {args.timeout_seconds}")
    print(f"Number of runs: {args.number_of_runs}")

    sys.exit(0)


