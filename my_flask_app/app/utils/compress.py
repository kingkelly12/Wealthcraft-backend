"""Gzip JSON responses for clients that accept it (phones do, and unpack it themselves)."""
import gzip

from flask import request

MIN_BYTES = 1400          # smaller than a network packet: not worth it


def gzip_response(response):
    if (response.direct_passthrough or response.status_code < 200 or response.status_code >= 300
            or 'Content-Encoding' in response.headers or response.mimetype != 'application/json'
            or 'gzip' not in request.headers.get('Accept-Encoding', '').lower()):
        return response
    body = response.get_data()
    if len(body) < MIN_BYTES:
        return response
    response.set_data(gzip.compress(body, compresslevel=5))
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-Length'] = str(len(response.get_data()))
    response.vary.add('Accept-Encoding')
    return response
