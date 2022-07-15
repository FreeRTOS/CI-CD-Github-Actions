import yaml
from yaml.loader import SafeLoader
import io
import os
import hashlib
from datetime import datetime
from argparse import ArgumentParser
from sbom_utils import *

spdx_version = 'SPDX-2.2'
data_license = 'CC0-1.0'
sbom_creator = 'Amazon Web Services'
sbom_namespace = 'https://github.com/aws/ota-for-aws-iot-embedded-sdk/blob/main/sbom.spdx'
url = 'https://github.com/aws/ota-for-aws-iot-embedded-sdk'
REPO_PATH = ''
    
def scan_overTheAir():
    dependency_path = os.path.join(REPO_PATH, 'source/dependency')
    path_3rdparty = os.path.join(REPO_PATH, 'source/dependency/3rdparty')
    manifest_path = os.path.join(REPO_PATH, 'manifest.yml')

    o = io.StringIO()
    buffer3rd = {}
    dependency_info = {}
    total_file_list = []
    dependency_file_list = {}
    with open(manifest_path) as f:
        manifest = yaml.load(f, Loader=SafeLoader)
    root_license = manifest['license']
    
    for dependency in manifest['dependencies']:
        buffer3rd[dependency['name']] = io.StringIO()
        dependency_info[dependency['name']] = dependency
        
    for subdir, dirs, files in os.walk(os.path.join(REPO_PATH, 'source')):
        if 'dependency' in subdir:
            continue
        for file in files:
            if file.endswith('.spdx'):
                continue
            filepath = os.path.join(subdir, file)
            file_checksum = hash_sha1(filepath)
            if file.endswith('.c'):
                file_writer(o, filepath, file, file_checksum, root_license)
            total_file_list.append(file_checksum)
    
    for library in os.listdir(dependency_path):
        if library.startswith('.'):
            continue
        if library == '3rdparty':
            continue
        library_lic = root_license
        try: 
            buffer = buffer3rd[library]
            library_lic = dependency_info[library]['license']
            dependency_file_list[library] = []
            temp_list = dependency_file_list[library]
        except:
            buffer = o
            temp_list = []
            
        for subdir, dirs, files in os.walk(os.path.join(dependency_path, library)):
            for file in files:
                filepath = os.path.join(subdir, file)
                file_checksum = hash_sha1(filepath)
                if file.endswith('.c'):
                    file_writer(buffer, filepath, file, file_checksum, library_lic)
                total_file_list.append(file_checksum)
                temp_list.append(file_checksum)

    for library in os.listdir(path_3rdparty):
        if library.startswith('.'):
            continue
        library_lic = root_license
        try: 
            buffer = buffer3rd[library]
            library_lic = dependency_info[library]['license']
            dependency_file_list[library] = []
            temp_list = dependency_file_list[library]
        except:
            buffer = o
            temp_list = []
        
        for subdir, dirs, files in os.walk(os.path.join(path_3rdparty, library)):
            for file in files:
                filepath = os.path.join(subdir, file)
                file_checksum = hash_sha1(filepath)
                if file.endswith('.c'):
                    file_writer(buffer, filepath, file, file_checksum, library_lic)
                total_file_list.append(file_checksum)
                temp_list.append(file_checksum)

    output = open('sbom.spdx', 'w')
    doc_writer(output, spdx_version, data_license, manifest['name'], sbom_namespace, sbom_creator)
    pacakge_writer(output, manifest['name'], manifest['version'], url, root_license, package_hash(total_file_list), description=manifest['description'])
    output.write(o.getvalue())
    #print packages
    for name, info in dependency_info.items():
        if len(dependency_file_list[name]) == 0:
            analyzed = False
        pacakge_writer(output, name, info['version'], info['repository']['url'], info['license'], package_hash(dependency_file_list[name]))
        output.write(buffer3rd[name].getvalue())
    
    #print relationships
    for dependency in dependency_info.keys():
        output.write('Relationship: SPDXRef-Package-' + manifest['name'] + ' DEPENDS_ON SPDXRef-Package-' + dependency + '\n')

if __name__ == "__main__":
    parser = ArgumentParser(description='SBOM generator')
    parser.add_argument('--repo-root-path',
                        type=str,
                        required=None,
                        default=os.getcwd(),
                        help='Path to the repository root.')
    args = parser.parse_args()
    REPO_PATH = os.path.abspath(args.repo_root_path)
    scan_overTheAir()
