#!/usr/bin/env python3

import os, sys
from yaml import load
from yaml import CLoader as Loader

from git import Repo
from argparse import ArgumentParser

REPO_PATH=''

# List of submodules excluded from manifest.yml file
IGNORE_SUBMODULES_LIST = []

# Obtain submodule path of all entries in manifest.yml file.
def read_manifest():
    dict = {}

    # Read YML file
    path_manifest = os.path.join(REPO_PATH, 'manifest.yml')
    assert os.path.exists(path_manifest), 'Missing manifest.yml'
    with open(path_manifest, 'r') as fp:
        manifest_data = fp.read()
    yml = load(manifest_data, Loader=Loader)
    assert 'dependencies' in yml, 'Manifest YML parsing error'

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
        assert 'version' in dep, "Failed to parse 'version/tag' for submodule"
        assert 'repository' in dep and 'path' in dep['repository'] and 'url' in dep['repository'], "Failed to parse 'repository' object for submodule"
        dict[dep['name']] = (dep['repository']['path'], dep['version'])

    return dict

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

    submodules_info_from_manifest = read_manifest()
    submodule_path_from_manifest = [pair[0] for pair in submodules_info_from_manifest.values()]
    submodule_path_from_manifest = sorted(submodule_path_from_manifest)

    submodules_info_from_git = get_all_submodules()
    submodule_path_from_git = sorted(submodules_info_from_git.keys())

    print(REPO_PATH)
    print('\nList of submoduled libraries being verified:', submodule_path_from_git)

    # Check that manifest.yml contains entries for all submodules
    # present in repository.
    if submodule_path_from_manifest != submodule_path_from_git:
        print('manifest.yml is missing entries for:')
        # Find list of library submodules missing in manifest.yml
        for git_path in submodule_path_from_git:
            if git_path not in submodule_path_from_manifest:
                print(git_path)
        sys.exit(1)

    # Verify that manifest contains correct versions of submodules pointers.
    mismatch_flag = False
    print('\nVerifying that manifest.yml versions are up-to-date.....')
    for submodule_name, submodule_info in submodules_info_from_manifest.items():
        relative_path = submodule_info[0]
        manifest_commit =  submodule_info[1]
        submodule = Repo(REPO_PATH+'/'+relative_path)
        submodule.remote('origin').fetch()
        submodule.git.checkout(manifest_commit)
        if (submodules_info_from_git[relative_path] != submodule.head.commit):
            print('manifest.yml does not have correct commit ID for', submodule_name,'manifest Commit=(',manifest_commit, submodule.head.commit,') Actual Commit=',submodules_info_from_git[relative_path])
            mismatch_flag = True
        
    if mismatch_flag and args.fail_on_incorrect_version:
        sys.exit(1)

    print('\nmanifest.yml file has been verified!')
    sys.exit(0)


