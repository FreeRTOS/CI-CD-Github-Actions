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

def needs_licenseref(license):
    #SPDX license list can be found at https://spdx.org/licenses/
    not_in_spdx = ["OASIS-IPR"]
    if license in not_in_spdx:
        return True
    return False

def scan_dir():
    print(f"DEBUG: Starting scan_dir function")
    print(f"DEBUG: REPO_PATH = {REPO_PATH}")
    print(f"DEBUG: SOURCE_PATH = {SOURCE_PATH}")
    print(f"DEBUG: SOURCE_PATH exists: {os.path.exists(SOURCE_PATH)}")
    
    dependency_path = os.path.join(REPO_PATH, 'source/dependency')
    path_3rdparty = os.path.join(REPO_PATH, 'source/dependency/3rdparty')
    manifest_path = os.path.join(REPO_PATH, 'manifest.yml')
    url = 'https://github.com/' + os.getenv('GITHUB_REPOSITORY')

    output_buffer = {}
    total_file_list = []
    dependency_info = {}
    dependency_file_list = {}
    licenseref_info = ""
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
        print(f"DEBUG: subdir={subdir}, dirs={dirs}, files={files}")
        if 'dependency' in subdir:
            continue
        for file in files:
            if file.endswith('.spdx'):
                continue
            filepath = os.path.join(subdir, file)
            file_checksum = hash_sha1(filepath)
            total_file_list.append(file_checksum)
            if file.endswith('.c') or file.endswith('.h'):
                file_writer(output_buffer[root_name], filepath.replace(SOURCE_PATH, ''), file_checksum, root_license)

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
                        file_writer(buffer, filepath.replace(SOURCE_PATH, ''), file_checksum, library_lic)
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
                        file_writer(buffer, filepath.replace(SOURCE_PATH, ''), file_checksum, library_lic)
                    total_file_list.append(file_checksum)
                    temp_list.append(file_checksum)

    #print sbom file to sbom.spdx
    output = open('sbom.spdx', 'w')
    doc_writer(output, manifest['version'], manifest['name'])
    package_writer(output, manifest['name'], manifest['version'], url, root_license, package_hash(total_file_list), description=manifest['description'])
    output.write(output_buffer[root_name].getvalue())

    #print dependencies
    for library_name in output_buffer.keys():
        if library_name == root_name:
            continue
        info = dependency_info[library_name]

        #Is this license part of the SPDX license list?  If not, then we need to use LicenseRef for proper SPDX validation
        if needs_licenseref(info['license']):
            license = "LicenseRef-" + info['license']
            licenseref_info += "\nLicenseID: LicenseRef-%s\n" % info['license']
            licenseref_info += "LicenseName: %s\n" % info['license']
            licenseref_info += "ExtractedText: <text>%s</text>\n" % info['license']
        else:
            license = info['license']

        package_writer(output, library_name, info['version'], info['repository']['url'], license, package_hash(dependency_file_list[library_name]))
        output.write(output_buffer[library_name].getvalue())
   
    #print relationships
    for library_name in output_buffer.keys():
        if library_name == root_name:
            continue
        output.write('Relationship: SPDXRef-Package-' + manifest['name'] + ' DEPENDS_ON SPDXRef-Package-' + library_name + '\n')

    #print any LicenseRef info
    if licenseref_info != "":
        output.write(licenseref_info)

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
    print(f"DEBUG: Parsed args - repo_root_path: {args.repo_root_path}, source_path: {args.source_path}")
    REPO_PATH = os.path.abspath(args.repo_root_path)
    SOURCE_PATH = os.path.abspath(args.source_path)
    print(f"DEBUG: Absolute paths - REPO_PATH: {REPO_PATH}, SOURCE_PATH: {SOURCE_PATH}")
   
    scan_dir()
