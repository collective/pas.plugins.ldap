from zope.component import queryUtility
from bda.cache import (
    Memcached,
    NullCache,
)
from .interfaces import ICacheSettingsRecordProvider


def cacheProviderFactory():
    recordProvider = queryUtility(ICacheSettingsRecordProvider)
    if not recordProvider:
        return NullCache()
    value = recordProvider().value or ''
    servers = value.split()
    if servers:
        return Memcached(servers)
    return NullCache()
