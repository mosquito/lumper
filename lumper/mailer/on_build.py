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
    if context.settings.options.mail_map:
        recepient = context.settings.options.mail_map.get(data['sender'], context.settings.options.admin_mail)
    else:
        recepient = context.settings.options.admin_mail
    email = Email(
        sender=context.settings.smtp.sender,
        recipient=recepient,
        subject="[%s] <%s> Build successful" % (data['tag'], data['name'])
    )

    email.append(
        "\n".join([
            "Build %s sucessful" % data['name'],
            "\n",
            "Sender: %s" % data['sender'],
            "Repository: %s" % data['repo'],
            "Commit: %s" % data['commit'],
            "Commit message: %s" % data['message'],
            "Tag: %s" % data['tag'],
            "Build timestamp: %s" % data['timestamp'],
            "Build date: %s" % datetime.fromtimestamp(data['timestamp']),
            "\nBuild log:\n\t%s" % "\n\t".join(data['build_log']),
        ]), mimetype="text/plain")

    return email.send(
        host=context.settings.smtp.host,
        port=context.settings.smtp.port,
        user=context.settings.smtp.user,
        password=context.settings.smtp.password,
        tls=context.settings.smtp.tls
    )