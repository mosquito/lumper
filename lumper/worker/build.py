#!/usr/bin/env python
# encoding: utf-8

import logging
import json
import os
import shutil
import traceback
import git
import re
import requests

from crew.worker import context, HandlerClass
from uuid import uuid4
from tempfile import gettempdir

log = logging.getLogger("builder")


class TemporaryFolder(object):

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

        if os.path.exists(self._dir):
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

            with TemporaryFolder() as path:
                self.prepare(path)
                try:
                    self.data.update({"id": self.build(path)})
                except Exception as e:
                    self.data.update({'error': e})

                self.data.update({'build_log': self.build_log})

            if self.data.get('status') and context.settings.options.docker_publish:
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
        repo, name = ["".join(list(i)[::-1]).replace('/', '_') for i in self.data['name'].lower()[::-1].split('/', 1)][::-1]

        if not context.settings.options.docker_registry:
            log.warning("PUSHING TO PUBLIC DOCKER REGISTRY.")
        else:
            name = ("%s/%s" % (repo, name)).lower()
            repo = ("%s/%s" % (registry, name)).lower()

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
            insecure_registry=not use_ssl,
            stream=True
        )

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
                log.debug(data)

        if registry:
            url = "%s://%s" % ('https' if use_ssl else 'http', registry)
            try:
                log.debug("Trying to fetch image id")
                img_id = filter(lambda x: str(x[0]) == str(tag), requests.get("%s/v1/repositories/%s/tags" % (url, name)).json().items())[0][1]
                log.info('Pushing successful as %s', img_id)
                log.debug("Deleting tag: latest")
                resp = requests.delete("%s/v1/repositories/%s/tags/latest" % (url, name))
                log.debug('%s', resp.json())

                log.debug("Setting latest tag as %s", img_id)
                resp = requests.put(
                    "%s/v1/repositories/%s/tags/latest" % (url, name),
                    '"%s"' % img_id,
                    headers={'Content-Type': 'application/json'}
                )
                log.debug('%s', resp.json())
            except Exception:
                self.build_log.append("ERROR: Can't fetch image id from registry \"%s\"" % url)

    def prepare(self, path):
        url = self.data['repo']
        log.info('Cloning repo "%s" => "%s"', url, path)
        res = self.git.clone(url, path)
        log.debug("Cloning result: %s", res)

        commit_hash = self.data['commit']
        log.info('Checkout commit "%s"', commit_hash)
        self.git.checkout(commit_hash)
        self.git.submodule("update", "--recursive", "--init")

        log.info('Updating submodules')
        for sm in git.Repo(path).submodules:
            log.info(' Updating submodule: "%s"', sm)
            sm.update(recursive=True, init=True)
            log.info(' Submodule "%s" updated', sm)

        self.restore_commit_times(path)

        log.info("Preparing complete")

    @staticmethod
    def restore_commit_times(path):

        log.info("Restoring file mtimes for path: %s", path)

        def walk(tree):
            ret = list()
            for i in tree:
                ret.append(i)
                if i.type == 'tree':
                    ret.extend(walk(i))
            return ret

        repo = git.Repo(path)

        def find_mtimes(repo):
            objects = walk(repo.tree())
            t = repo.head.commit
            tt = t.traverse()
            ret = {}
            while objects:
                hashes = set(i.binsha for i in walk(t.tree))
                # iterate over reversed list to be able to remove elements by index
                for n, i in reversed(list(enumerate(objects))):
                    if i.binsha not in hashes:
                        del objects[n]
                    else:
                        if i.path not in ret or t.authored_date < ret[i.path]:
                            ret[i.path] = t.authored_date
                try:
                    t = next(tt)
                except StopIteration:
                    break
            return ret

        for i, mtime in find_mtimes(repo).items():
            fname = os.path.join(path, i)
            log.debug("%s %s", mtime, fname)
            os.utime(fname.encode('utf-8'), (mtime, mtime))

        for sm in repo.submodules:
            sm_internal_path = os.path.join(repo.git_dir, 'modules', sm.name)
            if os.path.exists(sm_internal_path):
                sm_repo = git.Repo(sm_internal_path)
            else:
                sm_repo = git.Repo(sm.path)

            for i, mtime in find_mtimes(sm_repo).items():
                fname = os.path.join(path, sm.path, i)
                log.debug(u"%s %s", mtime, fname)
                os.utime(fname.encode('utf-8'), (mtime, mtime))

    def build(self, path):
        log.debug("Start building...")
        tag = ("%s:%s" % (self.data['name'], self.data['tag'].lstrip("v"))).lower()
        log.debug("Selecting tag: %s", tag)

        self.build_log = []
        log.debug('Building')
        try:
            for line in self.docker.build(path, rm=True, tag=tag):
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
                    log.error(chunk.get('error'))
                    raise StandardError(chunk['error'])
        except Exception as e:
            log.exception(e)

    def resolve_image_id(self, image_id):
        self.docker.images()


BuildHandler.bind("build")
