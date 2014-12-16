#!/usr/bin/env python
# encoding: utf-8
from __future__ import division, absolute_import
from ..json_handler import JSONRequest
from .. import register
import tornado.gen
from time import time


@register(r"/api/v1/heartbeat")
class HeartBeat(JSONRequest):
    SUPPORTED_METHODS = ('GET')

    @tornado.gen.coroutine
    def get(self):
        start = time()
        uuid, result, counter = yield self.settings['crew'].call('heartbeat')
        self.response({
            "delta": (result - start) * 1000,
            "uuid": uuid,
            "beats": counter
        })