#!/usr/bin/env python
# encoding: utf-8
import logging
import json
import os
import shutil
import traceback
import urllib
import git
import re

from collections import defaultdict
from crew.worker import context, HandlerClass
from uuid import uuid4
from tempfile import gettempdir
import time

log = logging.getLogger("builder")


class TempoaryFolder(object):
    def __init__(self):
        self._dir = os.path.join(gettempdir(), str(uuid4()))
        self._curdir = os.path.abspath(os.getcwd())

    def __enter__(self):
        assert not os.path.exists(self._dir)

        log.debug('Making directory: "%s"', self._dir)
        os.makedirs(self._dir)

        log.debug('Changing directory: "%s"', self._dir)
        os.chdir(self._dir)
        return self._dir

    def __exit__(self, exc_type, exc_val, exc_tb):
        log.debug('Changing directory: "%s"', self._curdir)
        os.chdir(self._curdir)

        log.debug('Deleting directory: "%s"', self._dir)
        shutil.rmtree(self._dir)


class BuildHandler(HandlerClass):
    STREAM_EXPR = {
        "build_success": re.compile("^Successfully built\s+(?P<id>\S+)\n?$")
    }

    def process(self):
        try:
            self.git = git.Git()
            self.docker = context.settings.docker

            with TempoaryFolder() as path:
                self.prepare(path)
                try:
                    self.data.update({"id": self.build(path)})
                except Exception as e:
                    self.data.update({'error': e})

                self.data.update({'build_log': self.build_log})

            if context.settings.options.docker_publish:
                self.push()

            return self.data
        except Exception as e:
            exc = Exception(repr(e))
            exc._tb = traceback.format_exc(e)
            exc.log = getattr(self, 'build_log', [])
            return exc

    def push(self):
        registry = context.settings.options.docker_registry
        use_ssl = context.settings.options.docker_ssl_registry

        tag = self.data['tag'].lstrip("v")
        repo, name = ["".join(list(i)[::-1]).replace('/', '_') for i in self.data['name'][::-1].split('/', 1)][::-1]

        if not context.settings.options.docker_registry:
            log.warning("PUSHING TO PUBLIC DOCKER REGISTRY.")
        else:
            name = "%s/%s" % (repo, name)
            repo = "%s/%s" % (registry, name)

            try:
                self.docker.tag(self.data['id'], repo, tag)
            except Exception as e:
                log.error(e)

        log.info(
            "Preparing to push to the registry: %s://%s",
            'https' if use_ssl else 'http', registry if registry else 'PUBLIC'
        )

        response = self.docker.push(
            repo, tag=tag,
            insecure_registry=not use_ssl, stream=True)

        self.build_log.append('')
        self.build_log.append(
            "Pushing into registry %s://%s" % ('https' if use_ssl else 'http', registry if registry else 'public')
        )

        for line in response:
            chunk = json.loads(line)
            data = chunk.get("status")
            if chunk.get('error'):
                self.data['status'] = False
                details = chunk.get('errorDetail', {}).get('message')
                log.error(details)
                self.build_log.append(details)
            else:
                log.info(data)
                self.build_log.append(data)

        # if description.get('error'):
        #     self.data['status'] = False
        #     self.build_log.append("Status: %s" % status.get('status'))
        #     self.build_log.append("Error: %s" % description.get("error"))
        #     self.build_log.append("Error details: %s" % description.get("errorDetail", {}).get("message"))
        # else:
        #     self.build_log.append("Status: %s" % status.get('status'))

    def prepare(self, path):
        url = self.data['repo']
        log.info('Cloning repo "%s" => "%s"', url, path)
        self.git.clone(url, path)

        commit_hash = self.data['commit']
        log.info('Checkout commit "%s"', commit_hash)
        self.git.checkout(commit_hash)

        log.info("Preparing complete")

    def build(self, path):
        tag = "%s:%s" % (self.data['name'], self.data['tag'].lstrip("v"))
        self.build_log = []
        for line in self.docker.build(path, pull=True, rm=True, forcerm=True, tag=tag):
            chunk = json.loads(line)
            stream = chunk.get("stream", "").rstrip("\n\r")
            if stream:
                success = self.STREAM_EXPR['build_success'].match(stream)
                self.build_log.append(stream)
                if success:
                    self.data['status'] = True
                    return success.groupdict()['id']
                else:
                    log.info(stream)

            elif chunk.get("error"):
                err = chunk['error'].strip("\n\r")
                log.error(err)
                self.build_log.append(err)
                raise StandardError(chunk['error'])

    def resolve_image_id(self, image_id):
        self.docker.images()


BuildHandler.bind("build")