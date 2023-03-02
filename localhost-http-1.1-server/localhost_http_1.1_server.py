from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread
import socket
import ssl
from argparse import ArgumentParser

LOCAL_HOST_IP = socket.gethostbyname("localhost")
PLAINTEXT_PORT = 8080
SSL_PORT = 4443

# Define a threaded HTTP server class
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_GET(self):
        # Receive the body of the request - don't do anything with it,
        # but this needs to be done to clear the receiving buffer.
        if self.headers.get('Content-Length') is not None:
            recv_content_len = int(self.headers.get('Content-Length'))
            recv_body = self.rfile.read(recv_content_len)

        # Always send a 200 response with "Hello" in the body.
        response_body = "Hello".encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)
    
    def do_PUT(self):
        # Receive the body of the request - don't do anything with it,
        # but this needs to be done to clear the receiving buffer.
        if self.headers.get('Content-Length') is not None:
            recv_content_len = int(self.headers.get('Content-Length'))
            recv_body = self.rfile.read(recv_content_len)

        # Always send a 200 response with "Hello" in the body.
        response_body = "Hello".encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def do_POST(self):
        # Receive the body of the request - don't do anything with it,
        # but this needs to be done to clear the receiving buffer.
        if self.headers.get('Content-Length') is not None:
            recv_content_len = int(self.headers.get('Content-Length'))
            recv_body = self.rfile.read(recv_content_len)

        # Always send a 200 response with "Hello" in the body.
        response_body = "Hello".encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)
    
    def do_HEAD(self):
        # Receive the body of the request - don't do anything with it,
        # but this needs to be done to clear the receiving buffer.
        if self.headers.get('Content-Length') is not None:
            recv_content_len = int(self.headers.get('Content-Length'))
            recv_body = self.rfile.read(recv_content_len)

        # Always send a 200 response with same headers as GET but without
        # response body
        response_body = "Hello".encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()

if __name__ == '__main__':
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

    # Create a plaintext HTTP server thread
    plaintext_http_server = ThreadedHTTPServer((LOCAL_HOST_IP, PLAINTEXT_PORT), SimpleHTTPRequestHandler)
    plaintext_http_server_thread = Thread(target=plaintext_http_server.serve_forever)
    plaintext_http_server_thread.start()

    # Create an SSL HTTP serve thread
    ssl_http_server = ThreadedHTTPServer((LOCAL_HOST_IP, SSL_PORT), SimpleHTTPRequestHandler)
    ssl_http_server.socket = ssl.wrap_socket(ssl_http_server.socket, keyfile=args.server_priv_key_path, certfile=args.server_cert_path, ca_certs=args.root_ca_cert_path, cert_reqs=ssl.CERT_OPTIONAL)
    ssl_http_server_thread = Thread(target=ssl_http_server.serve_forever)
    ssl_http_server_thread.start()

    plaintext_http_server_thread.join()
    ssl_http_server_thread.join()