import hashlib
from datetime import datetime

SPDX_VERSION = 'SPDX-2.2'
DATA_LICENSE = 'CC0-1.0'
CREATOR = 'Amazon Web Services'

def hash_sha1(file_path: str) -> str:
    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    with open(file_path, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()

def package_hash(file_list: str) -> str:
    sorted(file_list)
    h = hashlib.sha1("".join(file_list).encode())
    return h.hexdigest()

def file_writer(output, filepath: str, sha1: str, license: str, copyright='NOASSERTION', comment='NOASSERTION'):
    output.write('FileName: .'+ filepath + '\n')
    output.write('SPDXID: SPDXRef-File'+ filepath.replace('/', '-').replace('_', '') + '\n')
    output.write('FileChecksum: SHA1: '+ sha1 + '\n')
    output.write('LicenseConcluded: '+ license + '\n')
    output.write('FileCopyrightText: '+ copyright + '\n')
    output.write('FileComment: '+ comment + '\n')
    output.write('\n')

def package_writer(output, packageName: str, version: str, url: str, license: str, ver_code: str, file_analyzed=True,
                   copyright='NOASSERTION', summary='NOASSERTION', description='NOASSERTION', file_licenses='NOASSERTION'):
    output.write('PackageName: '+ packageName + '\n')
    output.write('SPDXID: SPDXRef-Package-'+ packageName + '\n')
    output.write('PackageVersion: '+ version + '\n')
    output.write('PackageDownloadLocation: '+ url + '\n')
    output.write('PackageLicenseDeclared: ' + license + '\n')
    output.write('PackageLicenseConcluded: '+ license + '\n')
    output.write('PackageLicenseInfoFromFiles: '+ file_licenses + '\n')
    output.write('FilesAnalyzed: '+ str(file_analyzed) + '\n')
    output.write('PackageVerificationCode: '+ ver_code + '\n')
    output.write('PackageCopyrightText: '+ copyright + '\n')
    output.write('PackageSummary: '+ summary + '\n')
    output.write('PackageDescription: '+ description + '\n')
    output.write('\n')

def doc_writer(output, version: str, name: str, creator_comment='NOASSERTION',
               doc_comment='NOASSERTION'):
    today = datetime.now()
    namespace = 'https://github.com/FreeRTOS/'+name+'/blob/'+version+'/sbom.spdx'
    output.write('SPDXVersion: ' + SPDX_VERSION + '\n')
    output.write('DataLicense: ' + DATA_LICENSE  + '\n')
    output.write('SPDXID: SPDXRef-DOCUMENT\n')
    output.write('DocumentName: ' + name + '\n')
    output.write('DocumentNamespace: ' + namespace + '\n')
    output.write('Creator: Organization:' + CREATOR + '\n')
    output.write('Created: ' + today.isoformat()[:-7] + 'Z\n')
    output.write('CreatorComment: ' + creator_comment + '\n')
    output.write('DocumentComment: ' + doc_comment + '\n')
    output.write('\n')
