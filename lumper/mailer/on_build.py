#!/usr/bin/env python
# encoding: utf-8
from crew.worker import context, Task

@Task("build.finished")
def on_build(data):
    return None