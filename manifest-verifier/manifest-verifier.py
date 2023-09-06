#!/usr/bin/env python3

import os, sys
from yaml import load
from yaml import CLoader as Loader

from git import Repo
from argparse import ArgumentParser

# At time of writing GitHub Runners will select Bash by default.
bashPass=   "\033[32;1mPASSED -"
bashInfo=   "\033[33;1mINFO -"
bashFail=   "\033[31;1mFAILED -"
bashEnd=    "\033[0m"

REPO_PATH=''

# List of submodules excluded from manifest.yml file
IGNORE_SUBMODULES_LIST = []

# Obtain submodule path of all entries in manifest.yml file.
def read_manifest(git_modules, path_manifest):
    list = []

    with open(git_modules, 'r') as fp:
        module_lines = fp.read()
    if "submodule" not in module_lines:
        print("{0} No submodules in the repo. Exiting. {1}".format(bashInfo, bashEnd))
        exit(0)

    with open(path_manifest, 'r') as fp:
        manifest_data = fp.read()
    yml = load(manifest_data, Loader=Loader)
    if "dependencies" not in yml:
        print("{0} No dependencies in {1}. Exiting {2}".format(bashInfo, path_manifest, bashEnd))
        exit(0)

    # Iterate over all the "dependencies" entries, verify that
    # each contains entries for the following hierarchy:
    # name: "<library-name>"
    # version: "<version>"
    # repository:
    #   type: "git"
    #   url: <library-github-url>
    #   path: <path-to-submodule-in-repository>
    #
    for dep in yml['dependencies']:
        assert 'version' in dep, f"Failed to parse 'version/tag' for submodule {dep}"
        assert 'repository' in dep, f"Failed to parse 'repository' for {dep}"
        assert 'path' in dep['repository'], f"Failed to parse 'path' for {dep}"
        assert 'url' in dep['repository'], f"Failed to parse 'repository' object for {dep}"
        
        list.append( ( dep['repository']['path'], dep['version'] ) )
        print("{0} Submodule {1}:{2} from manifest.yml {3}".format(bashInfo, dep['repository']['path'],dep['version'], bashEnd))
    return list

# Generate list of submodules path in repository, excluding the
# path in IGNORES_SUBMODULES_LIST.
def get_all_submodules():
    info_dict = {}
    repo = Repo(REPO_PATH)
    for submodule in repo.submodules:
        path = submodule.abspath.replace(REPO_PATH+'/', '')
        if path not in IGNORE_SUBMODULES_LIST:
            #print(path,':',submodule.module().head.commit)
            info_dict[path] = submodule.module().head.commit

    return info_dict

if __name__ == '__main__':
    parser = ArgumentParser(description='manifest.yml verifier')
    parser.add_argument('--repo-root-path',
                        type=str,
                        required=None,
                        default=os.getcwd(),
                        help='Path to the repository root.')
    parser.add_argument('--ignore-submodule-path',
                        type=str,
                        required=None,
                        help='Comma-separated list of submodules path to ignore.')
    parser.add_argument('--fail-on-incorrect-version',
                        action='store_true',
                        help='Flag to indicate script to fail for incorrect submodules versions in manifest.yml')

    args = parser.parse_args()

    if args.ignore_submodule_path != None:
        IGNORE_SUBMODULES_LIST = args.ignore_submodule_path.split(',')

    # Convert any relative path (like './') in passed argument to absolute path.
    REPO_PATH = os.path.abspath(args.repo_root_path)
    # Read YML file
    path_manifest = os.path.join(REPO_PATH, 'manifest.yml')
    assert os.path.exists(path_manifest), f"{bashFail} NO FILE {REPO_PATH}/manifest.yml {bashEnd}"

    git_modules = os.path.join(REPO_PATH, '.gitmodules')
    assert os.path.exists(path_manifest), f"{bashFail} NO FILE {REPO_PATH}/.gitmodules {bashEnd}"

    print("{0} PARSING manifest.yml FILE: {1}{2}".format(bashInfo, REPO_PATH, bashEnd))
    # Get a list of all the submodules from the manifest file
    submodules_info_from_manifest = read_manifest(git_modules, path_manifest)
    
    # Pull just the path from the tuple
    submodule_paths_from_manifest = [submodule[0] for submodule in submodules_info_from_manifest]

    # Get a dictionary of all the submodules from the .gitmodule file
    submodules_info_from_git = get_all_submodules()

    # Get just the paths from the dictionary
    submodule_path_from_git = submodules_info_from_git.keys()

    print("{0} CHECKING PATH: {1}{2}".format(bashInfo, REPO_PATH, bashEnd))
    
    print("{0} List of Submodules From Git being verified: {1}".format(bashInfo, bashEnd))
    for submodule_path in submodule_path_from_git:
        print("{0} {1} {2}".format(bashInfo, submodule_path, bashEnd))

    # Check that manifest.yml contains entries for all submodules present in repository.
    # Find list of library submodules missing in manifest.yml
    for git_path in submodule_path_from_git:
        if git_path not in submodule_paths_from_manifest:
            print(f"{bashFail} Submodule {git_path} not in manifest.yml paths: {submodule_paths_from_manifest} {bashEnd}")
            sys.exit(1)

    # Verify that manifest contains correct versions of submodules pointers.
    mismatch_flag = False
    print(f"{bashInfo} Verifying that manifest.yml versions are up-to-date..... {bashEnd}")
    # Loop over all the submodules we read from the manifest
    for submodule_name, manifest_commit in submodules_info_from_manifest:
        # Get the path to the submodule, then checkout the commit
        submodule = Repo(REPO_PATH+'/'+submodule_name)
        submodule.remote('origin').fetch()
        # Checkout the submodule from the commit in the manifest, there's an error
        submodule.git.checkout(manifest_commit)
        if (submodules_info_from_git[submodule_name] != submodule.head.commit):
            print("{0} manifest.yml does not have correct commit ID for {1}:\nManifest Commit=({2},{3}) Actual Commit={4} {5}"
                .format(bashFail, submodule_name, manifest_commit, submodule.head.commit, submodules_info_from_git[submodule_name], bashEnd))
            mismatch_flag = True

    if ( True == mismatch_flag ) and args.fail_on_incorrect_version:
        print(f"{bashFail} MISMATCHES WERE FOUND IN THE MANIFEST. EXITING WITH FAILURE DUE {bashEnd}")
        sys.exit(1)
    elif ( True == mismatch_flag ):
        print(f"{bashInfo} MISMATCHES WERE FOUND IN THE MANIFEST. EXITING WITH SUCCESS AS FAIL ON INCORRECT VERSION WAS NOT SET {bashEnd}")

    print("{0} manifest.yml file has been verified!{1}". format(bashPass, bashEnd))
    sys.exit(0)


