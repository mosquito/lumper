#!/usr/bin/env python
# encoding: utf-8
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging import getLogger
import smtplib
from crew.worker import context, Task


class Email(object):
    log = getLogger('emailer.email')

    def __init__(self, sender, recipient, subject, headers={}):
        self.__sent = False
        self.msg = MIMEMultipart('alternative')
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

@Task("build.finished")
def on_build(data):
    if isinstance(data, Exception):
        email = Email(
            sender=context.settings.smtp.sender,
            recipient=context.settings.options.admin_mail,
            subject="Build exception"
        )

        email.append(
            "Build log: \n\t%s\n\nError: %r\n\nTraceback: %s\n" % ("\n\t".join(data.log), data, data._tb),
            mimetype="text/plain"
        )
    else:
        if context.settings.options.mail_map:
            recepient = context.settings.options.mail_map.get(data['sender'], context.settings.options.admin_mail)
        else:
            recepient = context.settings.options.admin_mail

        email = Email(
            sender=context.settings.smtp.sender,
            recipient=recepient,
            subject="[%s] <%s> Build %s" % (data.get('tag'), data.get('name'), 'successful' if data.get('status') else 'failed')
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
                "Build date: %s" % datetime.fromtimestamp(data['timestamp']) if data.get('timestamp') else None,
                "\nBuild log:\n\t%s" % "\n\t".join(data.get('build_log')),
            ]))

    return email.send(
            host=context.settings.smtp.host,
            port=context.settings.smtp.port,
            user=context.settings.smtp.user,
            password=context.settings.smtp.password,
            tls=context.settings.smtp.tls
        )