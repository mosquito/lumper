#!/usr/bin/env python
# encoding: utf-8
import tornado.web
import json
import traceback
import logging

log = logging.getLogger("handlers.json")

class JSONRequest(tornado.web.RequestHandler):
    INDENT = None
    ENCODING = 'utf-8'
    ENSURE_ASCII = False
    SORT_KEYS = False
    __json = None

    def options(self, *args, **kwargs):
        self.finish()

    def prepare(self):
        self.clear_header('Content-Type')
        self.set_header('Access-Control-Allow-Methods', ", ".join(self.SUPPORTED_METHODS))
        self.set_header('Access-Control-Allow-Headers', "accept, origin, content-type, cookie")
        self.set_header('Access-Control-Allow-Credentials', 'true')
        self.set_header('Access-Control-Max-Age', 3600)

        if self.request.method == 'OPTIONS':
            return self.finish()

        self.content_type = 'application/json'
        self.set_header("Content-Type", "application/json; charset=%s" % self.ENCODING.lower())

    @property
    def json(self):
        if self.__json:
            return self.__json
        else:
            if self.content_type in self.request.headers.get('Content-Type', ''):
                try:
                    self.__json = json.loads(self.request.body) if self.request.body else {}
                    return self.__json
                except Exception as e:
                    log.debug(traceback.format_exc())
                    log.error(repr(e))
                    self.write_error(400)

    @staticmethod
    def default(obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, '_to_json'):
            return obj._to_json()
        else:
            return str(obj)

    def _jsonify(self, data):
        default = self.default
        return json.dumps(
            data,
            indent=self.INDENT,
            sort_keys=self.SORT_KEYS,
            ensure_ascii=self.ENSURE_ASCII,
            encoding=self.ENCODING,
            default=default
        )

    def response(self, data, finish=False):
        if not self._finished:
            self.write(self._jsonify(data))
            if finish:
                self.finish()