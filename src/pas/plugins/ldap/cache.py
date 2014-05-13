# -*- coding: utf-8 -*-
from bda.cache import Memcached
from bda.cache import NullCache
from pas.plugins.ldap.interfaces import ICacheSettingsRecordProvider
from zope.component import queryUtility


def cacheProviderFactory():
    recordProvider = queryUtility(ICacheSettingsRecordProvider)
    if not recordProvider:
        return NullCache()
    value = recordProvider().value or ''
    servers = value.split()
    if servers:
        return Memcached(servers)
    return NullCache()
