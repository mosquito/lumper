#!/usr/bin/env python
# encoding: utf-8

from time import time
import tornado.web
import tornado.gen
import hmac
import hashlib
import re
import arrow

from ..json_handler import JSONRequest
from .. import register
from tornado.gen import Future
from tornado.log import app_log as log

REXP={
    "split_refs": re.compile("^refs\/(?P<key>\S+)\/(?P<value>\S+)")
}

@register("/github/webhook/")
@register("/webhook/github")
class GitHubWebHookHandler(JSONRequest):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        self.delivery = self.request.headers.get("X-Github-Delivery")
        self.event = self.request.headers.get("X-Github-Event")

        is_valid = self.event and self.delivery and self.verify() if self.settings['args'].github_secret else None

        if is_valid:
            handler = getattr(self, "event_%s" % self.event, lambda: self.response("OK"))
            resp = handler()

            if isinstance(resp, Future):
                ret = yield resp
            else:
                ret = resp

            if not self._finished:
                self.finish(ret)
        else:
            self.send_error(403)
            if not self._finished:
                self.finish()

    def verify(self):
        signature = self.request.headers.get("X-Hub-Signature")
        h = hmac.new(self.settings['args'].github_secret, self.request.body, hashlib.sha1)
        return "sha1=%s" % h.hexdigest() == signature

    def event_ping(self):
        """ Just ping. """
        log.debug("Got PING request: %s", self.json)
        self.send_error(204)

    def event_push(self):
        """ Any Git push to a Repository, including editing tags or branches. Commits via API actions that update
        references are also counted. This is the default event."""
        return self._process_tag()

    def _process_tag(self):
        matcher = REXP['split_refs'].match(self.json.get('ref', ""))
        if matcher:
            refs = matcher.groupdict()
            if refs['key'] == 'tags':
                tag = refs['value']
                commit = self.json.get("head_commit")
                data = {
                    "tag": tag,
                    "repo": self.json['repository']['ssh_url'],
                    "commit": commit['id'],
                    "message": commit['message'],
                    "timestamp": arrow.get(commit['timestamp']).timestamp,
                    "name": self.json['repository']['full_name'],
                    "sender": self.json['sender']['login']
                }

                self.settings['crew'].call("build", data, routing_key="crew.tasks.build.finished", expiration=self.settings.get('timeout', 600))
                self.response(True)
        else:
            self.response(False)

    # def event_commit_comment(self):
    #     """ Any time a Commit is commented on. """
    # def event_delete(self):
    #     """ Any time a Branch or Tag is deleted. """
    # def event_deployment(self):
    #     """ Any time a Repository has a new deployment created from the API. """
    # def event_deployment_status(self):
    #     """ Any time a deployment for a Repository has a status update from the API. """
    # def event_fork(self):
    #     """ Any time a Repository is forked. """
    # def event_gollum(self):
    #     """ Any time a Wiki page is updated. """
    # def event_issue_comment(self):
    #     """ Any time an Issue is commented on. """
    # def event_issues(self):
    #     """ Any time an Issue is assigned, unassigned, labeled, unlabeled, opened, closed, or reopened. """
    # def event_member(self):
    #     """ Any time a User is added as a collaborator to a non-Organization Repository. """
    # def event_membership(self):
    #     """ Any time a User is added or removed from a team. Organization hooks only. """
    # def event_page_build(self):
    #     """ Any time a Pages site is built or results in a failed build. """
    # def event_public(self):
    #     """ Any time a Repository changes from private to public. """
    # def event_pull_request_review_comment(self):
    #     """ Any time a Commit is commented on while inside a Pull Request review (the Files Changed tab). """
    # def event_pull_request(self):
    #     """ Any time a Pull Request is assigned, unassigned, labeled, unlabeled, opened, closed, reopened, or
    #     synchronized (updated due to a (selevent_f):new push in the branch that the pull request is tracking)."""
    # def event_repository(self):
    #     """ Any time a Repository is created. Organization hooks only. """
    # def event_release(self):
    #     """ Any time a Release is published in a Repository. """
    # def event_status(self):
    #     """ Any time a Repository has a status update from the API """
    # def event_team_add(self):
    #     """ Any time a team is added or modified on a Repository. """
    # def event_watch(self):
    #     """ Any time a User watches a Repository. """


@register("/webhook/gitlab")
class CommonWebHookHandler(JSONRequest):

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        matcher = REXP['split_refs'].match(self.json.get('ref', ""))
        if matcher:
            refs = matcher.groupdict()
            if refs['key'] == 'tags':
                tag = refs['value']
                commit = self.json.get('commits', [])
                commit = commit[0] if commit else {}

                repo_name = self.json['repository']['homepage'].split("/")
                repo_name = "%s/%s" % (repo_name.pop(-2), repo_name.pop())

                data = {
                    "tag": tag,
                    "repo": self.json['repository']['url'],
                    "commit": self.json['checkout_sha'],
                    "message": commit.get('message', '<No message>'),
                    "timestamp": arrow.get(commit.get('timestamp', time())).timestamp,
                    "name": repo_name,
                    "sender": str(self.json['user_id']),
                }

                self.settings['crew'].call("build", data, routing_key="crew.tasks.build.finished", expiration=self.settings.get('timeout', 600))
                self.response(True)
        else:
            self.response(False)
