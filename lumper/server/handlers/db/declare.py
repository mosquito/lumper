#!/usr/bin/env python
# encoding: utf-8
import pymongo
import logging

log = logging.getLogger("db.declare")

def declare(db):
    log.debug("Declaring database scheme")
    db.environments.ensure_index([("name", pymongo.ASCENDING), ("unique", True)])
    db.environments.ensure_index([("vlan", pymongo.ASCENDING), ("unique", True)])
    db.environments.ensure_index([("name", pymongo.HASHED)])
    db.environments.ensure_index([("vlan", pymongo.HASHED)])
    db.images.ensure_index([("hash", pymongo.HASHED)])
    db.images.ensure_index([("role", pymongo.HASHED)])
    db.images.ensure_index([("parent", pymongo.HASHED)])
