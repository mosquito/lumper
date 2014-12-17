#!/usr/bin/env python
# encoding: utf-8
import argparse
import logging
import sys
import os
from tornado.log import LogFormatter


class LogSetterAction(argparse.Action):
    FORMAT = u'[%(asctime)s] %(filename)s:%(lineno)d %(levelname)-6s %(message)s'

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")

        root = logging.getLogger()
        handler = logging.StreamHandler()
        handler.setFormatter(LogFormatter(color='color' in os.environ.get('TERM', '')))
        root.setLevel(logging.INFO)
        root.handlers = [handler]
        super(self.__class__, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        self.setter(values)
        setattr(namespace, self.dest, values)

    def setter(self, level='info'):
        root = logging.getLogger()

        level = getattr(logging, level.upper(), logging.INFO)
        lvl = root.level if not level else level
        root.setLevel(lvl)

        root.info('Logging level is "{0}"'.format(logging._levelNames[lvl]))