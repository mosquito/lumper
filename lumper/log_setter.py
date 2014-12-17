#!/usr/bin/env python
# encoding: utf-8
import argparse
import logging
import sys


class LogSetterAction(argparse.Action):
    FORMAT = u'[%(asctime)s] %(filename)s:%(lineno)d %(levelname)-6s %(message)s'

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")

        logging.basicConfig(format=self.FORMAT, level=logging.INFO)
        super(self.__class__, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        self.setter(values)
        setattr(namespace, self.dest, values)

    def setter(self, level='info'):
        root = logging.getLogger()

        level = getattr(logging, level.upper(), logging.INFO)

        fmt = root.handlers[0].formatter
        if root.handlers:
            for handler in root.handlers:
                root.removeHandler(handler)

        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(fmt)

        lvl = root.level if not level else level

        root.addHandler(handler)
        root.setLevel(lvl)

        root.info('Logging level is "{0}"'.format(logging._levelNames[lvl]))