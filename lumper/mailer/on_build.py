#!/usr/bin/env python
# encoding: utf-8
from datetime import datetime
import json
import urllib2
from crew.worker import context, Task
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import Encoders
import logging
import smtplib


class Attachment(object):
    pass


class FileAttachment(Attachment):
    def __init__(self, data, file_name, content_type="application/octet-stream"):
        self.part = MIMEBase('application', "octet-stream")
        self.part.set_payload(data.encode('utf-8'))
        Encoders.encode_base64(self.part)
        self.part.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(file_name))

    def attach(self, email):
        assert isinstance(email, Email)
        email.add_part(self.part)


class Email(object):
    log = logging.getLogger('emailer.email')

    def __init__(self, sender, recipient, subject, headers={}):
        self.__sent = False
        self.msg = MIMEMultipart()
        self.msg['Subject'] = subject
        self.msg['From'] = sender
        self.msg['To'] = recipient
        self.log.debug("Building message from <%s> to <%s>", sender, recipient)
        for key, value in headers.iteritems():
            self.log.debug('Add header "%s": "%s"', key, value)
            self.msg[key] = value

    def __setitem__(self, key, value):
        self.log.debug('Setting header "%s": "%s"', key, value)
        self.msg[key] = value

    def __getitem__(self, item):
        return self.msg[item]

    def get(self, key, default=None):
        if key in self.msg:
            return self.msg[key]
        else:
            return default

    def add_part(self, part):
        assert isinstance(part, MIMEBase)
        self.msg.attach(part)

    def append(self, part, mimetype='plain'):
        prt = unicode(part)
        self.log.debug('Adding "%s" (length: %s) part to message from <%s> to <%s>', mimetype, len(prt), self.msg['From'], self.msg['To'])
        self.msg.attach(MIMEText(prt, mimetype, _charset='utf-8'))

    def send(self, host='localhost', port=25, tls=False, user=None, password=None):
        self.log.info("Sending message for <%s>.", self.msg['To'])
        self.log.debug("Connecting to SMTP server %s:%d", host, port)
        if not self.__sent:
            connect = smtplib.SMTP(host, port=port)
            try:
                connect.ehlo()
                if tls:
                    self.log.debug("Establishing TLS")
                    connect.starttls()
                    connect.ehlo()
                if user:
                    connect.login(user=user, password=password)
                connect.sendmail(self.msg['From'], self.msg['To'], self.msg.as_string())
                self.__sent = True
                return True
            except Exception as e:
                self.log.exception(e)
                self.log.error("Error: %r", e)
                self.__sent = False
                return False
            finally:
                connect.close()
        else:
            self.log.error("Message already sent")
            return False

log = logging.getLogger('emailer.task')

@Task("build.finished")
def on_build(data):
    if isinstance(data, Exception):
        email = Email(
            sender=context.settings.smtp.sender,
            recipient=context.settings.options.admin_mail,
            subject="Build exception"
        )

        email.append("Error: %r\n\nTraceback: %s\n\n" % (data, getattr(data, '_tb', "No traceback")))

        FileAttachment(
            "\n".join(getattr(data, "log", ['No log',])),
            file_name='build_log.txt',
            content_type='text/plain'
        ).attach(email)

    else:
        if context.settings.options.mail_map:
            recepient = context.settings.options.mail_map.get(data['sender'], context.settings.options.admin_mail)
        else:
            recepient = context.settings.options.admin_mail

        email = Email(
            sender=context.settings.smtp.sender,
            recipient=recepient,
            subject="[%s] <%s> Build %s" % (
                data.get('tag'),
                data.get('name'),
                'successful' if data.get('status') else 'failed'
            )
        )


        email.append(
            "\n".join([
                "Build %s %s" % (data.get('name'), 'successful' if data.get('status') else 'failed'),
                "\n",
                "Sender: %s" % data.get('sender'),
                "Repository: %s" % data.get('repo'),
                "Commit: %s" % data.get('commit'),
                "Commit message: %s" % data.get('message'),
                "Tag: %s" % data.get('tag'),
                "Build timestamp: %s" % data.get('timestamp'),
                "Build date: %s" % datetime.utcfromtimestamp(data['timestamp']) if data.get('timestamp') else None,
                "\n\n"
            ]))

        FileAttachment(
            "\n".join(data.get('build_log')),
            file_name='build_log.txt',
            content_type='text/plain'
        ).attach(email)

        if context.settings.options.build_hooks:
            hook_data = json.dumps(data, sort_keys=False, encoding="utf-8")
            for url in context.settings.options.build_hooks:
                try:
                    log.info('Sending build data to: "%s"', url)
                    req = urllib2.Request(url)
                    req.add_header('Content-Type', 'application/json')
                    response = urllib2.urlopen(req, hook_data, timeout=3)
                    log.info('Build hook response for "%s": HTTP %d', url, response.code)
                except Exception as e:
                    if log.getEffectiveLevel() <= logging.DEBUG:
                        log.exception(e)
                    log.error("Build hook error: %r", e)

    return email.send(
            host=context.settings.smtp.host,
            port=context.settings.smtp.port,
            user=context.settings.smtp.user,
            password=context.settings.smtp.password,
            tls=context.settings.smtp.tls
        )
