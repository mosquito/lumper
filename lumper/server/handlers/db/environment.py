#!/usr/bin/env python
# encoding: utf-8
import logging
from flask import jsonify
from ... import route, RESTView

log = logging.getLogger("handlers.environment")

@route("/api/v1/environments", methods=("get", "post", "options"))
class Environments(RESTView):
    def get(self, *args, **kwargs):
        return jsonify({"args": args, "kw": kwargs})