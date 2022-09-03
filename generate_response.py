import os
import datetime
import mimetypes

from config import OK, PROTOCOL, ERRORS


class GenerateResponse:
    def __init__(self, code, method, uri):
        self.code = code
        self.method = method
        self.uri = uri

    def byte_format(self):
        start_line = self.generate_start_line()
        headers = self.generate_headers()
        body = self.generate_body()
        response = ('{start_line}\r\n{headers}\r\n\r\n'.format(
            start_line=start_line,
            headers=headers
        )).encode('utf-8')

        if body:
            response += body

        return response

    def generate_start_line(self):
        return '{protocol} {code} {msg}'.format(
            protocol=PROTOCOL,
            code=self.code,
            msg=ERRORS[self.code]
        )

    def generate_headers(self):
        headers = {
            'Date': self.get_date(),
            'Server': 'otus@gmail.com',
            'Content-Length': self.get_file_size(),
            'Content-Type': mimetypes.guess_type(self.uri)[0],
            'Connection': 'close'
        }
        headers = "\r\n".join("{key}: {value}".format(key=key, value=value) for key, value in headers.items())
        return headers

    def generate_body(self):
        if self.code == OK and self.method != "GET":
            return None

        with open(self.uri, "rb") as file:
            body = file.read()

        return body

    @classmethod
    def get_date(cls):
        return datetime.datetime.now().ctime()

    def get_file_size(self):
        return os.path.getsize(self.uri)