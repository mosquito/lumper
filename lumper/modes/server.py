#!/usr/bin/env python
# encoding: utf-8
import os
import tornado.ioloop
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.log import app_log as log
from lumper.server import HANDLERS
from crew.master.tornado import Client
from pika import PlainCredentials


def run(args):
    crew_client = Client(
        host=args.rmq_address, port=args.rmq_port, virtualhost=args.rmq_vhost,
        credentials=PlainCredentials(username=args.rmq_user, password=args.rmq_password)
    )

    app = Application(
        args=args,
        handlers=HANDLERS,
        xsrf_cookies=False,
        cookie_secret=args.cookie_secret,
        debug=args.debug,
        reload=args.debug,
        gzip=args.gzip,
        crew=crew_client,
        timeout=args.timeout
    )

    http_server = HTTPServer(app, xheaders=True)
    http_server.listen(args.port, address=args.address)
    log.info('Server started {host}:{port}'.format(host=args.address, port=args.port))

    try:
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        log.exception(e)
        log.fatal("Server aborted by error: %r", e)

    return 0
