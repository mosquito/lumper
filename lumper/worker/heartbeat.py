#!/usr/bin/env python
# encoding: utf-8

from crew.worker import context, Task
from time import time

@Task("heartbeat")
def heartbeat(data):
    context.settings.heartbeat_counter += 1
    return context.settings.uuid, time(), context.settings.heartbeat_counter