import yaml
from yaml.loader import SafeLoader
import io
import os
import hashlib
from datetime import datetime
from argparse import ArgumentParser
from sbom_utils import *

REPO_PATH = ''
SOURCE_PATH = ''

def scan_dir():
    dependency_path = os.path.join(REPO_PATH, 'source/dependency')
    path_3rdparty = os.path.join(REPO_PATH, 'source/dependency/3rdparty')
    manifest_path = os.path.join(REPO_PATH, 'manifest.yml')
    url = 'https://github.com/' + os.getenv('GITHUB_REPOSITORY')

    output_buffer = {}
    total_file_list = []
    dependency_info = {}
    dependency_file_list = {}
    with open(manifest_path) as f:
        manifest = yaml.load(f, Loader=SafeLoader)
    root_license = manifest['license']
    root_name = manifest['name']
    url += '/tree/' + manifest['version']
    output_buffer[root_name] = io.StringIO()
    
    try:
        for dependency in manifest['dependencies']:
            dependency_info[dependency['name']] = dependency
    except Exception:
        pass

    #scan the source code
    for subdir, dirs, files in os.walk(SOURCE_PATH):
        if 'dependency' in subdir:
            continue
        for file in files:
            if file.endswith('.spdx'):
                continue
            filepath = os.path.join(subdir, file).replace(SOURCE_PATH, '')
            file_checksum = hash_sha1(filepath)
            total_file_list.append(file_checksum)
            if file.endswith('.c'):
                file_writer(output_buffer[root_name], filepath, file_checksum, root_license)

    #scan dependencies
    if os.path.exists(dependency_path):
        for library in os.listdir(dependency_path):
            if library.startswith('.') or library == '3rdparty':
                continue

            #cross check with manifest file
            if library in dependency_info.keys():
                output_buffer[library] = io.StringIO()
                buffer = output_buffer[library]
                library_lic = dependency_info[library]['license']
                dependency_file_list[library] = []
                temp_list = dependency_file_list[library]
            else:
                library_lic = root_license
                buffer = output_buffer[root_name]
                temp_list = []
            
            for subdir, dirs, files in os.walk(os.path.join(dependency_path, library)):
                for file in files:
                    filepath = os.path.join(subdir, file)
                    file_checksum = hash_sha1(filepath)
                    if file.endswith('.c'):
                        file_writer(buffer, filepath, file_checksum, library_lic)
                    total_file_list.append(file_checksum)
                    temp_list.append(file_checksum)

    #scan 3rd party code
    if os.path.exists(path_3rdparty):
        for library in os.listdir(path_3rdparty):
            if library.startswith('.'):
                continue

            #cross check with manifest file
            if library in dependency_info.keys():
                output_buffer[library] = io.StringIO() 
                buffer = output_buffer[library]
                library_lic = dependency_info[library]['license']
                dependency_file_list[library] = []
                temp_list = dependency_file_list[library]
            else:
                library_lic = root_license
                buffer = output_buffer[root_name]
                temp_list = []
            
            for subdir, dirs, files in os.walk(os.path.join(path_3rdparty, library)):
                for file in files:
                    filepath = os.path.join(subdir, file)
                    file_checksum = hash_sha1(filepath)
                    if file.endswith('.c'):
                        file_writer(buffer, filepath, file_checksum, library_lic)
                    total_file_list.append(file_checksum)
                    temp_list.append(file_checksum)

    #print sbom file to sbom.spdx
    output = open('sbom.spdx', 'w')
    doc_writer(output, manifest['version'], manifest['name'])
    pacakge_writer(output, manifest['name'], manifest['version'], url, root_license, package_hash(total_file_list), description=manifest['description'])
    output.write(output_buffer[root_name].getvalue())

    #print dependencies
    for library_name in output_buffer.keys():
        if library_name == root_name:
            continue
        info = dependency_info[library_name]
        pacakge_writer(output, library_name, info['version'], info['repository']['url'], info['license'], package_hash(dependency_file_list[library_name]))
        output.write(output_buffer[library_name].getvalue())
    
    #print relationships
    for library_name in output_buffer.keys():
        if library_name == root_name:
            continue
        output.write('Relationship: SPDXRef-Package-' + manifest['name'] + ' DEPENDS_ON SPDXRef-Package-' + library_name + '\n')

if __name__ == "__main__":
    parser = ArgumentParser(description='SBOM generator')
    parser.add_argument('--repo-root-path',
                        type=str,
                        required=None,
                        default=os.getcwd(),
                        help='Path to the repository root.')
    parser.add_argument('--source-path',
                        type=str,
                        required=None,
                        default=os.path.join(os.getcwd(), 'source'),
                        help='Path to the source code dir.')
    args = parser.parse_args()
    REPO_PATH = os.path.abspath(args.repo_root_path)
    SOURCE_PATH = os.path.abspath(args.source_path)
    
    scan_dir()
