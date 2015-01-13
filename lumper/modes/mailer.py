#!/usr/bin/env python
# encoding: utf-8
from collections import namedtuple

from crew.worker import Listener, Context, NODE_UUID, UUID
from pika import PlainCredentials
from crew.worker import context
import logging
import lumper.mailer

def run(args):
    log = logging.getLogger("main")
    try:
        SMTPSettings = namedtuple("SmtpSettings", "host port user password tls sender")
        Listener(
            port=args.amqp_port,
            host=args.amqp_address,
            credentials=PlainCredentials(username=args.amqp_user, password=args.amqp_password) if args.amqp_user else None,
            virtual_host=args.amqp_vhost,
            handlers=context.handlers,
            set_context=Context(
                options=args,
                node_uuid=NODE_UUID,
                uuid=UUID,
                smtp=SMTPSettings(
                    host=args.smtp_host,
                    port=args.smtp_port,
                    user=args.smtp_user,
                    password=args.smtp_password,
                    tls=args.smtp_tls,
                    sender=args.smtp_sender
                )
            ),
        ).loop()
    except Exception as e:
        if logging.getLogger().level < logging.INFO:
            log.exception(e)
        else:
            log.fatal("Exiting by fatal error: %s", e)
    return 0
