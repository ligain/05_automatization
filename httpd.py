import argparse
import mimetypes
import os
import logging
import multiprocessing
from socket import AF_INET, SOCK_STREAM, socket, SOL_SOCKET, SO_REUSEADDR
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import unquote_plus


HOST = 'localhost'
PORT = 8080
MAX_HEADER_LENGH = 65536


class HttpCode:
    OK = (200, 'OK')
    BAD_REQUEST = (400, 'Bad Request')
    FORBIDDEN = (403, 'Forbidden')
    NOT_FOUND = (404, 'Not Found')
    METHOD_NOT_ALLOWED = (405, 'Method Not Allowed')
    HEADER_TOO_LARGE = (431, 'Request Header Fields Too Large')


class HeaderTooLong(Exception):
    pass


class BadRequest(Exception):
    pass


class OtusRequestHandler:
    server_version = 'OTUS server/0.1'
    http_protocol = 'HTTP/1.1'
    read_buf_size = -1
    write_buf_size = 0

    def __init__(self, client_addr, client_sock, document_root=None):
        self.document_root = document_root if document_root else os.getcwd()
        self.client_addr = client_addr
        self.client_sock = client_sock
        self.path = ''
        self.method = ''
        self.headers = {}
        self.rfile = client_sock.makefile('rb', self.read_buf_size)
        self.wfile = client_sock.makefile('wb', self.write_buf_size)

    def handle(self):
        logging.info('Got connection from: %s', self.client_addr)
        try:
            self.parse_request()
        except HeaderTooLong:
            self.send_error(*HttpCode.HEADER_TOO_LARGE)
            self.close_connection()
            return
        except BadRequest:
            self.send_error(*HttpCode.BAD_REQUEST)
            self.close_connection()
            return

        if hasattr(self, self.method.lower()):
            method = getattr(self, self.method.lower())
            method()
        else:
            logging.info('Unknown method: %s', self.method)
            self.send_error(*HttpCode.METHOD_NOT_ALLOWED)

        self.close_connection()

    def close_connection(self):
        if not self.wfile.closed:
            try:
                self.wfile.flush()
            except OSError:
                logging.exception('Error while closing client connection:')
        self.wfile.close()
        self.rfile.close()

        logging.info('Client connection %s is closed', self.client_addr)
        self.client_sock.close()

    def parse_request(self):
        request_line = str(self.rfile.readline(), 'iso-8859-1')
        if not request_line.endswith('\r\n'):
            raise BadRequest
        raw_request = request_line.rstrip('\r\n')
        parts = raw_request.split()
        if len(parts) == 3:
            self.method, self.path, self.protocol = parts
        elif len(parts) == 2:
            self.method, self.path = parts
        else:
            logging.error('Invalid request header with parts: %s', parts)
            raise BadRequest

        # Parse request headers
        while True:
            line = self.rfile.readline()
            if len(line) > MAX_HEADER_LENGH:
                logging.error('Header to large: %s', line)
                raise HeaderTooLong
            if line in (b'\r\n', b'\n', b''):
                break
            decoded_header_line = line.decode('iso-8859-1')
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
        path = os.path.normpath(path)
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

    def send_headers(self, code, status, content_length, ctype):
        self.send_response_header(code, status)
        self.send_header("Server", self.server_version)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", content_length)
        self.send_header("Connection", "close")
        self.end_headers()

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
        try:
            dir_list = os.listdir(dir_path)
        except OSError:
            logging.exception('Error getting directory')
            self.send_error(*HttpCode.NOT_FOUND)
            return

        if "index.html" in dir_list:
            # get index.html as default dir file
            full_index_path = os.path.join(dir_path, 'index.html')
            return self.retrieve_file(full_index_path)
        else:
            logging.info('Try to get directory w/o index.html')
            self.send_error(*HttpCode.NOT_FOUND)
            return

    def retrieve_file(self, file_path):
        logging.info('Getting file: {}'.format(file_path))
        try:
            file = open(file_path, 'rb')
        except IOError:
            logging.exception('Error reading file')
            self.send_error(*HttpCode.NOT_FOUND)
            return

        file_mime_type, _ = mimetypes.guess_type(file_path)
        if file_mime_type is None:
            file_mime_type = "application/octet-stream"

        with file:
            file_content = file.read()
            self.send_headers(*HttpCode.OK, len(file_content), file_mime_type)
            return file_content

    def process_get_and_head(self):
        converted_path = self.convert_path()

        if converted_path is None:
            self.send_error(*HttpCode.NOT_FOUND)
            return
        elif os.path.isdir(converted_path):
            content_bytes = self.list_directory(converted_path)
        elif os.path.isfile(converted_path):
            content_bytes = self.retrieve_file(converted_path)
        else:
            self.send_error(*HttpCode.FORBIDDEN)
            return
        return content_bytes

    def get(self):
        logging.info('Processing GET request: {}'.format(self.path))
        content_bytes = self.process_get_and_head()
        if not content_bytes:
            logging.error('Sending an empty response in GET request')
            return
        self.wfile.write(content_bytes)

    def head(self):
        logging.info('Processing HEAD request: {}'.format(self.path))
        self.process_get_and_head()


def run_server(address, backlog=5, max_workers=5, document_root=None):
    pool = ThreadPoolExecutor(max_workers)
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(address)
    sock.listen(backlog)
    logging.info('Started OTUS server on: %s with max_workers: %d',
                 address, max_workers)
    while True:
        client_sock, client_addr = sock.accept()
        request_handler = OtusRequestHandler(client_addr, client_sock, document_root)
        pool.submit(request_handler.handle)


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
        level=logging.INFO
    )

    parser = argparse.ArgumentParser(description='Otus HTTP server')
    parser.add_argument(
        '-r', '--docroot',
        help='Path to the root server directory [default: cwd]',
        default=os.getcwd()
    )
    parser.add_argument(
        '-w', '--workers',
        help='Number of workers to serve [default: num of CPU cores]',
        type=int,
        default=multiprocessing.cpu_count()
    )
    args = parser.parse_args()
    run_server(
        address=(HOST, PORT),
        max_workers=args.workers,
        document_root=args.docroot
    )
