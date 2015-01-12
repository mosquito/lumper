#!/usr/bin/env python
# encoding: utf-8

from crew.worker import Listener, Context, NODE_UUID, UUID
from pika import PlainCredentials
from crew.worker import context
import logging
import lumper.mailer

def run(args):
    log = logging.getLogger("main")
    try:
        Listener(
            port=args.amqp_port,
            host=args.amqp_address,
            credentials=PlainCredentials(username=args.amqp_user, password=args.amqp_password) if args.amqp_user else None,
            virtual_host=args.amqp_vhost,
            handlers=context.handlers,
            set_context=Context(options=args, node_uuid=NODE_UUID, uuid=UUID)
        ).loop()
    except Exception as e:
        if logging.getLogger().level < logging.INFO:
            log.exception(e)
        else:
            log.fatal("Exiting by fatal error: %s", e)
    return 0
