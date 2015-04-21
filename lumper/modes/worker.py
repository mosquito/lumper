#!/usr/bin/env python
# encoding: utf-8
from crew.worker import Listener, Context, NODE_UUID, UUID
from pika import PlainCredentials
from crew.worker import context
import logging
import docker
import docker.tls
import lumper.worker


def run(args):
    log = logging.getLogger("main")

    if args.docker_tls:
        tls = docker.tls.TLSConfig(client_cert=(args.docker_client_cert, args.docker_client_key),
                                   ca_cert=args.docker_ca_cert, assert_hostname=False)
    else:
        tls = False

    docker_client = docker.Client(base_url=args.docker_url, tls=tls, timeout=300)
    docker_client.verify = args.docker_tls_strict

    try:
        log.info('Testing docker connection: %s', args.docker_url)
        docker_client.info()

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
                heartbeat_counter=0,
                docker=docker_client
            )
        ).loop()
    except Exception as e:
        if logging.getLogger().level < logging.INFO:
            log.exception(e)
        else:
            log.fatal("Exiting by fatal error: %s", e)
    return 0
