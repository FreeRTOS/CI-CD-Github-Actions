import random
from OpenSSL import crypto, SSL

# File names for generated credentials
ROOT_CA_PRIV_KEY_FILE = "root_ca_priv_key.key"
ROOT_CA_CERT_FILE = "root_ca_cert.crt"
SERVER_PRIV_KEY_FILE = "server_priv_key.key"
SERVER_CERT_FILE = "server_cert.crt"
DEVICE_PRIV_KEY_FILE = "device_priv_key.key"
DEVICE_CERT_FILE = "device_cert.crt"

# Reusable certificate subject for testing
TEST_CERT_SUBJECT = crypto.X509Name(crypto.X509().get_subject())
TEST_CERT_SUBJECT.C = 'US'
TEST_CERT_SUBJECT.ST = 'Test_ST'
TEST_CERT_SUBJECT.L = 'Test_L'
TEST_CERT_SUBJECT.O = 'Test_O'
TEST_CERT_SUBJECT.OU = 'Test_OU'
TEST_CERT_SUBJECT.CN = 'localhost'
TEST_CERT_SUBJECT.emailAddress = 'test@test.com'

# Common name has to be different for the Root CA according to OpenSSL documents
TEST_CERT_SUBJECT_ROOT_CA = crypto.X509Name(TEST_CERT_SUBJECT)
TEST_CERT_SUBJECT_ROOT_CA.CN = 'localhostrootca'

def generate_priv_keys_and_certs():

    # Root CA generation

    ca_key_pair = crypto.PKey()
    ca_key_pair.generate_key(crypto.TYPE_RSA, 2048)
    ca_cert = crypto.X509()
    ca_cert.set_subject(TEST_CERT_SUBJECT_ROOT_CA)
    ca_cert.set_serial_number(random.getrandbits(64))
    ca_cert.gmtime_adj_notBefore(0)
    ca_cert.gmtime_adj_notAfter(31536000)
    ca_cert.set_issuer(TEST_CERT_SUBJECT_ROOT_CA)
    ca_cert.set_pubkey(ca_key_pair)
    ca_cert.sign(ca_key_pair, "sha256")
    open(ROOT_CA_PRIV_KEY_FILE, "w").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, ca_key_pair).decode("utf-8"))
    open(ROOT_CA_CERT_FILE, "w").write(crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert).decode("utf-8"))

    # Server credential generation

    server_key_pair = crypto.PKey()
    server_key_pair.generate_key(crypto.TYPE_RSA, 2048)
    server_cert = crypto.X509()
    server_cert.set_subject(TEST_CERT_SUBJECT)
    server_cert.set_serial_number(random.getrandbits(64))
    server_cert.gmtime_adj_notBefore(0)
    server_cert.gmtime_adj_notAfter(31536000)
    server_cert.set_issuer(ca_cert.get_subject())
    server_cert.set_pubkey(server_key_pair)
    server_cert.sign(ca_key_pair, "sha256")
    open(SERVER_PRIV_KEY_FILE, "w").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, server_key_pair).decode("utf-8"))
    open(SERVER_CERT_FILE, "w").write(crypto.dump_certificate(crypto.FILETYPE_PEM, server_cert).decode("utf-8"))

    # Device credential generation

    device_key_pair = crypto.PKey()
    device_key_pair.generate_key(crypto.TYPE_RSA, 2048)
    device_cert = crypto.X509()
    device_cert.set_subject(TEST_CERT_SUBJECT)
    device_cert.set_serial_number(random.getrandbits(64))
    device_cert.gmtime_adj_notBefore(0)
    device_cert.gmtime_adj_notAfter(31536000)
    device_cert.set_issuer(ca_cert.get_subject())
    device_cert.set_pubkey(device_key_pair)
    device_cert.sign(ca_key_pair, "sha256")
    open(DEVICE_PRIV_KEY_FILE, "w").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, device_key_pair).decode("utf-8"))
    open(DEVICE_CERT_FILE, "w").write(crypto.dump_certificate(crypto.FILETYPE_PEM, device_cert).decode("utf-8"))

if __name__ == "__main__":
    generate_priv_keys_and_certs()
