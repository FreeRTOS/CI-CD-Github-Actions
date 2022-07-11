import yaml
from yaml.loader import SafeLoader
import io
import os
from argparse import ArgumentParser
from sbom_utils import *

spdx_version = 'SPDX-2.2'
data_license = 'CC0-1.0'
sbom_creator = 'Amazon Web Services'
sbom_namespace = 'https://github.com/aws/Device-Defender-for-AWS-IoT-embedded-sdk/blob/main/sbom.spdx'
url = 'https://github.com/aws/Device-Defender-for-AWS-IoT-embedded-sdk'
REPO_PATH = ''

def scan_deviceDefender():
    manifest_path = os.path.join(REPO_PATH, 'manifest.yml')

    o = io.StringIO()
    buffer3rd = {}
    dependency_info = {}
    total_file_list = []
    dependency_file_list = {}
    with open(manifest_path) as f:
        manifest = yaml.load(f, Loader=SafeLoader)
    root_license = manifest['license']

        
    for subdir, dirs, files in os.walk(os.path.join(REPO_PATH, 'source')):
        for file in files:
            if file.endswith('.spdx'):
                continue
            filepath = os.path.join(subdir, file)
            file_checksum = hash_sha1(filepath)
            if file.endswith('.c'):
                file_writer(o, filepath, file, file_checksum, root_license)
            total_file_list.append(file_checksum)
    

    output = open('sbom.spdx', 'w')
    doc_writer(output, spdx_version, data_license, manifest['name'], sbom_namespace, sbom_creator)
    pacakge_writer(output, manifest['name'], manifest['version'], url, root_license, package_hash(total_file_list), description=manifest['description'])
    output.write(o.getvalue())


if __name__ == "__main__":
    parser = ArgumentParser(description='SBOM generator')
    parser.add_argument('--repo-root-path',
                        type=str,
                        required=None,
                        default=os.getcwd(),
                        help='Path to the repository root.')
    args = parser.parse_args()
    REPO_PATH = os.path.abspath(args.repo_root_path)
    scan_deviceDefender()
