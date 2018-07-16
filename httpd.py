import argparse
import logging
import multiprocessing
import os
import io

from threading import Thread
from urllib.parse import unquote_plus
from socketserver import TCPServer, StreamRequestHandler
from functools import partial

from constants import HttpCode

HOST = 'localhost'
PORT = 8080


class OtusRequestHandler(StreamRequestHandler):
    server_version = 'Otus server/0.1'

    def __init__(self, *args, document_root=None, **kwargs):
        self.document_root = document_root
        self.method = ''
        self.protocol = 'HTTP/1.1'
        self.path = ''
        self.headers = {}
        super().__init__(*args, **kwargs)

    def handle(self):
        logging.info('Got connection from: %s', self.client_address)
        self.parse_request()
        if hasattr(self, self.method.lower()):
            method = getattr(self, self.method.lower())
            method()
        else:
            logging.info('Unknown method: %s', self.method)
            self.send_error(*HttpCode.METHOD_NOT_ALLOWED)

    def parse_request(self):
        request_line = str(self.rfile.readline(), 'utf8')
        self.raw_request = request_line.rstrip('\r\n')
        parts = self.raw_request.split()
        if len(parts) == 3:
            self.method, self.path, self.protocol = parts
        elif len(parts) == 2:
            self.method, self.path = parts
        else:
            logging.info('Invalid request header')

        # Parse request headers
        while True:
            line = self.rfile.readline()
            if line in (b'\r\n', b'\n', b''):
                break
            decoded_header_line = line.decode('utf8')
            decoded_header_line = decoded_header_line.rstrip('\r\n')
            name, body = decoded_header_line.split(': ')
            self.headers[name] = body

    def convert_path(self, path=None):
        """
        Converts url path to local filesystem path.
        Reads url path from self.path variable
        """
        if path is None:
            path = self.path
        path = path.split('?', 1)[0]
        path = unquote_plus(path)
        path = path.strip('/')
        full_path = os.path.join(self.document_root, path)
        if not os.path.exists(full_path):
            return
        return full_path

    def send_response_header(self, code, msg):
        """
        Adds first line in HTTP response in format:
        `protocol version` `http code` `http message`
        """
        response_header_str = "{protocol} {code} {msg}\r\n".format(
            protocol=self.protocol,
            code=code,
            msg=msg
        )
        self.wfile.write(response_header_str.encode("latin-1"))

    def send_header(self, key, value):
        header_str = "{}: {}\r\n".format(key, value)
        self.wfile.write(header_str.encode("latin-1"))

    def end_headers(self):
        self.wfile.write(b"\r\n")

    def send_error(self, code, status):
        self.send_response_header(code, status)
        self.send_header("Server", self.server_version)
        self.send_header("Connection", "close")
        self.end_headers()

    def list_directory(self, dir_path):
        # if dir_path.endswith("index.html"):
        #     # get index.html as default dir file
        #     pass
        try:
            dir_list = os.listdir(dir_path)
            if "index.html" in dir_list:
                # get index.html as default dir file
                pass
        except OSError:
            self.send_error(*HttpCode.NOT_FOUND)
            return

        response_str = "Listing of directory:\n"

    def retrieve_file(self, file_path):
        pass

    def guess_contenttype(self, file_path, extensions_map=None):
        pass

    def get(self):
        logging.info('Processing GET request: {}'.format(self.path))
        converted_path = self.convert_path()
        response_content = ""

        if converted_path is None:
            self.send_error(*HttpCode.NOT_FOUND)
            return
        elif os.path.isdir(converted_path):
            response_content = self.list_directory(converted_path)
        elif os.path.isfile(converted_path):
            pass
        else:
            self.send_error(*HttpCode.FORBIDDEN)
            return

        if response_content is not None:
            pass

        self.send_response_header(*HttpCode.OK)
        self.send_header("Server", self.server_version)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content‐Length", len(response_content))
        self.send_header("Connection", "close")
        self.end_headers()
        # write response content
        response_bytes = io.BytesIO(b"Hello")
        self.wfile.write(response_bytes.read())

    def head(self):
        logging.info('Processing HEAD request: {}'.format(self.path))


def run_server(serv):
    """ Run instance of TCP server """
    host, port = serv.server_address
    logging.info('Start worker to serve on host: %s, port: %s', host, port)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        logging.info('Keyboard interrupt received, exiting.')
        serv.shutdown()


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
        level=logging.INFO
    )

    parser = argparse.ArgumentParser(description='Otus HTTP server')
    parser.add_argument(
        '-r', '--docroot',
        help='Path to the root server directory',
        default=os.getcwd()
    )
    parser.add_argument(
        '-w', '--workers',
        help='Number of workers to serve',
        type=int,
        default=multiprocessing.cpu_count()
    )
    args = parser.parse_args()

    handler = partial(OtusRequestHandler, document_root=args.docroot)
    serv = TCPServer((HOST, PORT), handler)
    for _ in range(args.workers):
        tread = Thread(target=run_server, args=(serv, ))
        tread.daemon = True
        tread.start()
    run_server(serv)
