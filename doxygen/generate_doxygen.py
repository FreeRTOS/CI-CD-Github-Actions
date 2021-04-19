#!/usr/bin/env python3
import subprocess
import sys
import argparse
import os
import zipfile

# Executes the passed command in a shell subprocess.
# Returns True if any output is received from the shell process.
def run_cmd(cmd):
    """
    Execute the input command on the shell.
    """
    print(f"Executing command: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            encoding="utf-8",
            check=True,
            timeout=180,
        )
        print( result.stdout )
        return (len(result.stdout) > 0)
    except subprocess.CalledProcessError as e:
        result = e.stdout
        return result

def get_lib_paths(root, lib_parent_dirs):
    """
    Get all of the paths, relative to the root, to the libraries for which doxygen
    output has to be generated.
    """
    abs_lib_paths = []
    print("Root: %s", root)
    print(lib_parent_dirs)

    for lib_parent_dir in lib_parent_dirs:
        abs_lib_path_dir = os.path.join(root, lib_parent_dir)
        lib_path_dirs = os.listdir(abs_lib_path_dir)
        # Determine if it is a library path by checking if the directory contains "docs/doxygen"
        abs_lib_paths += [os.path.join(abs_lib_path_dir, dir) for dir in lib_path_dirs if os.path.exists(os.path.join(abs_lib_path_dir, dir, "docs", "doxygen"))]

    return abs_lib_paths


def main():
    """
    Generate documentation and optionally zip it up.
    """
    parser = argparse.ArgumentParser(description="Generate all doxygen and optionally zip it.")
    parser.add_argument("-r", "--root", action="store", required=False, dest="root", help="Repository root path. This defaults to the current working directory.")
    parser.add_argument("-d", "--library-directories", action="store", required=True, dest="lib_dirs", help="Comma-separate list of parent directories of libraries. These should be relative to repository root.")
    parser.add_argument("-z", "--zip", action="store_true", required=False, help="Zip all doxygen output.")
    args = parser.parse_args()
    repo_root = args.root
    doZip = args.zip

    # If the root folder is not give, use the current working directory.
    if( repo_root == None ):
        repo_root = os.getcwd()

    # Get the absolute paths to all of the libraries in the repository.
    abs_repo_root = os.path.abspath(repo_root)
    abs_lib_paths = get_lib_paths(abs_repo_root, args.lib_dirs.split(','))
    abs_doxy_paths = []
    doxygen_warnings_flag = False

    # Generate the doxygen for all of the libraries.
    for abs_lib_path in abs_lib_paths:
        abs_doxy_path = os.path.join(abs_lib_path, "docs", "doxygen")
        os.chdir(abs_lib_path)
        print(abs_lib_path)
        # If there is something printed by doxygen, then it represents a warning.
        doxygen_warnings_flag = run_cmd("doxygen docs/doxygen/config.doxyfile") or doxygen_warnings_flag
        abs_doxy_paths.append(abs_doxy_path)

    # Generate the doxygen for the repository to use the tags from the libraries.
    if os.path.exists(os.path.join(abs_repo_root,"docs","doxygen")):
        os.chdir(abs_repo_root)
        print(abs_repo_root)
        doxygen_warnings_flag = run_cmd("doxygen docs/doxygen/config.doxyfile") or doxygen_warnings_flag
        abs_doxy_paths.append(os.path.join(abs_repo_root, "docs", "doxygen"))

    # Zip up if desired.
    if not(doxygen_warnings_flag) and doZip:
        os.chdir(abs_repo_root)
        print(f"Zipping up to {abs_repo_root}{os.path.sep}doxygen.zip...")
        doxy_zip = zipfile.ZipFile("doxygen.zip", mode="w")
        try:
            for abs_doxy_path in abs_doxy_paths:
                abs_output_dir = os.path.join(abs_doxy_path, "output")
                for out_root, _, out_files in os.walk(abs_output_dir):
                    rel_out_root = os.path.relpath(out_root, abs_repo_root)
                    for out_file in out_files:
                        doxy_zip.write(os.path.join(rel_out_root, out_file))
        finally:
            doxy_zip.close()

    # Return failure exit code if doxygen generation resulted in warnings.
    if doxygen_warnings_flag == False:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
