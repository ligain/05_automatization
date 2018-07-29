import argparse
import os
import logging
import multiprocessing
from socket import AF_INET, SOCK_STREAM, socket, SOL_SOCKET, SO_REUSEADDR
from concurrent.futures import ThreadPoolExecutor


class OtusRequestHandler:
    server_version = 'OTUS server/0.1'
    http_protocol = 'HTTP/1.1'

    def __init__(self, client_addr, client_sock, document_root=None):
        self.document_root = document_root if document_root else os.getcwd()
        self.client_addr = client_addr
        self.client_sock = client_sock
        self.path = ''
        self.method = ''
        self.raw_request = b''
        self.headers = {}

    def handle(self):
        logging.info('Got connection from: %s', self.client_addr)
        self.parse_request()

        self.client_sock.sendall(b'Hello')
        logging.info('Client connection %s closed', self.client_addr)
        self.client_sock.close()

    def parse_request(self):
        while True:
            msg = self.client_sock.recv(8192)
            if not msg:
                break
            self.raw_request += msg
        print(1)


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
        address=('', 8080),
        max_workers=args.workers,
        document_root=args.docroot
    )
