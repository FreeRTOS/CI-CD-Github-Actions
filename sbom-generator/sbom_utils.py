import hashlib
from datetime import datetime

def hash_sha1(file_path):
    BLOCKSIZE = 65536
    hasher = hashlib.sha1()
    with open(file_path, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()

def package_hash(file_list):
    sorted(file_list)
    h = hashlib.sha1("".join(file_list).encode())
    return h.hexdigest()

def file_writer(o, filepath, filename, sha1, license, copyright='NOASSERTION', comment='NOASSERTION'):
    o.write('FileName: '+ filename + '\n')
    o.write('SPDXID: SPDXRef-File-'+ filename.replace('/', '-') + '\n')
    o.write('FileChecksum: SHA1: '+ hash_sha1(filepath) + '\n')
    o.write('LicenseConcluded: '+ license + '\n')
    o.write('FileCopyrightText: '+ copyright + '\n')
    o.write('FileComment: '+ comment + '\n')
    o.write('\n')
    
    
def pacakge_writer(o, packageName, version, url, license, ver_code, file_analyzed=True, 
                   copyright='NOASSERTION', summary='NOASSERTION', description='NOASSERTION'):
    o.write('PackageName: '+ packageName + '\n')
    o.write('SPDXID: SPDXRef-Package-'+ packageName + '\n')
    o.write('PackageVersion: '+ version + '\n')
    o.write('PackageDownloadLocation: '+ url + '/tree/' + version + '\n')
    o.write('PackageLicenseConcluded: '+ license + '\n')
    o.write('FilesAnalyzed: '+ str(file_analyzed) + '\n')
    o.write('PackageVerificationCode: '+ ver_code + '\n')
    o.write('PackageCopyrightText: '+ copyright + '\n')
    o.write('PackageSummary: '+ summary + '\n')
    o.write('PackageDescription: '+ description + '\n')
    o.write('\n')

def doc_writer(o, version, license, name, namespace, creator, creator_comment='NOASSERTION', 
               doc_comment='NOASSERTION'):
    today = datetime.now()
    o.write('SPDXVersion: ' + version + '\n')
    o.write('DataLicense: ' + license + '\n')
    o.write('SPDXID: SPDXRef-DOCUMENT' + '\n')
    o.write('DocumentName: ' + name + '\n')
    o.write('DocumentNamespace: ' + namespace + '\n')
    o.write('Creator: ' + creator + '\n')
    o.write('Created: ' + today.isoformat()[:-7] + 'Z\n')
    o.write('CreatorComment: ' + creator_comment + '\n')
    o.write('DocumentComment: ' + doc_comment + '\n')
    o.write('\n')
