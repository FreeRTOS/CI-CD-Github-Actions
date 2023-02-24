from argparse import ArgumentParser
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl

if __name__ == "__main__":
    # Parse passed in credentials
    parser = ArgumentParser(description='Localhost MQTT broker.')

    parser.add_argument('--root-ca-cert-path',
                        type=str,
                        required=True,
                        help='Path to the root CA certificate.')
    parser.add_argument('--server-cert-path',
                        type=str,
                        required=True,
                        help='Path to the server certificate.')
    parser.add_argument('--server-priv-key-path',
                        type=str,
                        required=True,
                        help='Path to the private key')
    args = parser.parse_args()

    httpd = HTTPServer(('localhost', 443), BaseHTTPRequestHandler)

    httpd.socket = ssl.wrap_socket (httpd.socket,
            ca_certs=args.root_ca_cert_path,
            keyfile=args.server_priv_key_path, 
            certfile=args.server_cert_path,
            cert_reqs=ssl.CERT_OPTIONAL,
            server_side=True)

    httpd.serve_forever()

