#!/usr/bin/env python
# encoding: utf-8
from functools import wraps
import logging
from flask_api import FlaskAPI
from flask import Response, request, abort

log = logging.getLogger("lumper")
app = FlaskAPI('lumper')


class RESTView(object):
    def __init__(self, methods, credentials=True, age=None, origin='*', expose_headers=None, headers=None):
        self.methods = methods
        self.credentials = credentials
        self.age = age
        self.origin = origin
        self.expose_headers = expose_headers
        self.headers = headers

    def __call__(self, *args, **kwargs):
        method = request.method.lower()
        return getattr(self, method)(*args, **kwargs)

    def get(self, *args, **kwargs):
        raise NotImplementedError("Method not implemented")

    def post(self, *args, **kwargs):
        raise NotImplementedError("Method not implemented")

    def put(self, *args, **kwargs):
        raise NotImplementedError("Method not implemented")

    def patch(self, *args, **kwargs):
        raise NotImplementedError("Method not implemented")

    def head(self, *args, **kwargs):
        return Response("", headers=self._response_headers())

    def options(self, *args, **kwargs):
        return Response("", headers=self._response_headers())

    def _response_headers(self):
        headers = {
            "Access-Control-Allow-Methods": ", ".join([i.upper() for i in self.methods]),
            "Access-Control-Allow-Credentials": 'true' if self.credentials else 'false',
            "Access-Control-Max-Age": 0 if not self.age else int(self.age),
            "Access-Control-Allow-Origin": self.origin() if not callable(self.origin) else self.origin,
            "Access-Control-Expose-Headers": ", ".join(self.expose_headers),
            "Access-Control-Allow-Headers": ", ".join(self.headers),
        }

        for h,v in headers.items():
            if not v:
                headers.pop(h)

        return headers


def route(url, methods=("OPTIONS", "GET", "PUT", "DELETE", "HEAD", "PATCH"), **kw):
    def deco(cls):
        assert issubclass(cls, RESTView)

        @wraps(cls)
        def wrap(*args, **kwargs):
            try:
                rest_obj = cls(methods, **kw)
                return rest_obj(*args, **kwargs)
            except NotImplementedError:
                return abort(405)

        log.debug("Registering route %r as class %r", url, cls)
        return app.route(url, methods=methods)(wrap)
    return deco
