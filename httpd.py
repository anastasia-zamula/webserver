import socket
import logging
import multiprocessing
import argparse

from config import QUEUE_SIZE, CHUNK_SIZE, MAX_LENGTH_REQUEST
from generate_response import GenerateResponse
from http_request_parser import HTTPRequestParser


class HTTPServer:
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM

    def __init__(self, host='localhost', port=8080,
                 doc_root='doc_root', queue_size=QUEUE_SIZE,
                 chunk_size=CHUNK_SIZE):
        self.host = host
        self.port = port
        self.doc_root = doc_root
        self.queue_size = queue_size
        self.chunk_size = chunk_size
        self.socket = socket.socket(self.address_family, self.socket_type)

    def start(self):
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
        except (OSError, TypeError):
            logging.error("Server don't start", exc_info=True)
            self.shutdown()

        logging.info("Server started on {}:{}".format(self.host, self.port))
        self.socket.listen(self.queue_size)

    def listen(self):
        try:
            client_socket = None
            client_address = ''
            while True:
                try:
                    client_socket, client_address = self.socket.accept()
                    logging.info("Request from {}".format(client_address))
                    self.handle(client_socket, client_address)
                except OSError:
                    logging.exception("listen exception from {}".format(client_address))
                    if client_socket:
                        client_socket.close()
        finally:
            self.shutdown()

    def handle(self, client_socket, address):
        try:
            request = self.receive(client_socket)
            if not request:
                logging.info("Empty request from {}".format(address))
                return

            code, method, uri = HTTPRequestParser.parser(request, self.doc_root)
            generate_response = GenerateResponse(code, method, uri)
            the_response = generate_response.byte_format()
            client_socket.sendall(the_response)
            logging.info("Send response to {}: {}, {}, {}".format(address, code, method, uri))
        except ConnectionError:
            err_msg = "Can't send response to {}".format(address)
            logging.exception(err_msg)
        finally:
            client_socket.close()

    def receive(self, client_socket):
        data = ""
        try:
            while True:
                chunk = client_socket.recv(CHUNK_SIZE)
                data += chunk.decode()
                if "\r\n\r\n" in data or not chunk or len(data) > MAX_LENGTH_REQUEST:
                    break
        except:
            logging.exception("receive exception from {}".format(self.host))

        return data

    def shutdown(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            logging.info("Server's socket closed")
        except OSError:
            return


def set_logging(logging_level=logging.INFO, filename=''):
    logging.basicConfig(
        level=logging_level,
        filename=filename,
        format='%(asctime)s %(levelname)s '
               '{%(pathname)s:%(lineno)d}: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def parse_args():
    parser = argparse.ArgumentParser(description='HTTPServer OTUS')

    parser.add_argument(
        '-hs', '--host', type=str, default="localhost",
        help='host, default: localhost'
    )
    parser.add_argument(
        '-p', '--port', type=int, default=9090,
        help='port, default: 9090'
    )
    parser.add_argument(
        '-w', '--workers', type=int, default=5,
        help='server workers count, default: 5'
    )
    parser.add_argument(
        '-d', '--dir_root', type=str, default='doc_root',
        help='DIRECTORY_ROOT with site files, default: doc_root'
    )
    parser.add_argument(
        '-l', '--log', type=str, default='log.log',
        help='path to log file, default: "log.log"'
    )

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    set_logging(logging.INFO, args.log)
    http_server = HTTPServer(host=args.host, port=args.port, doc_root=args.dir_root)
    http_server.start()
    workers = []
    try:
        for i in range(args.workers):
            worker = multiprocessing.Process(target=http_server.listen)
            workers.append(worker)
            worker.start()
            logging.info("{} worker started".format(i + 1))
        for worker in workers:
            worker.join()
    except KeyboardInterrupt:
        for worker in workers:
            if worker:
                worker.terminate()
    finally:
        logging.info("HTTPServer shutdown")
        http_server.shutdown()