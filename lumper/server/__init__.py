#!/usr/bin/env python
# encoding: utf-8
from functools import wraps
import logging

log = logging.getLogger("handlers")

HANDLERS = []

def register(*urls):
    def deco(cls):
        global HANDLERS

        for url in urls:
            HANDLERS.append((url, cls))
            log.debug('Register URL %r as %r' % (url, cls))

        @wraps(cls)
        def wrap(*args, **kwargs):
            return cls(*args, **kwargs)

        return wrap
    return deco

import handlers