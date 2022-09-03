import os
from urllib import parse

from config import OK, FORBIDDEN, NOT_FOUND, METHOD_NOT_ALLOWED


class HTTPRequestParser:
    methods = ["GET", "HEAD"]

    @classmethod
    def parser(cls, request, doc_root):
        request_head = request.split('\r\n')[0]
        method, uri, protocol = request_head.split()
        code = cls.get_code(method)

        if code != OK:
            return code, method, cls.get_name_file_error(code)

        code, uri = cls.validate_uri(uri, doc_root)

        if code != OK:
            uri = cls.get_name_file_error(code)

        return code, method, uri

    @classmethod
    def get_code(cls, method):
        if method not in cls.methods:
            return METHOD_NOT_ALLOWED
        return OK

    @classmethod
    def validate_uri(cls, uri, doc_root):
        uri_path = parse.unquote(uri)
        uri_path = uri_path.partition("?")[0]
        uri_path = os.path.join(doc_root, uri_path.lstrip('/'))

        if '../' in uri_path:
            return FORBIDDEN, uri

        if uri_path.endswith('/'):
            uri_path = os.path.join(uri_path, 'index.html')
            if not os.path.isfile(uri_path):
                return NOT_FOUND, uri_path

        if not os.path.isfile(uri_path):
            return NOT_FOUND, uri_path

        return OK, uri_path

    @staticmethod
    def get_name_file_error(code):
        name_file_error = '{}.html'.format(code)
        dir_path = os.path.dirname(os.path.abspath(__file__))
        dir_path = os.path.abspath(os.path.join(dir_path, "errors_html"))
        name_file_error = os.path.abspath(os.path.join(dir_path, name_file_error))
        return name_file_error