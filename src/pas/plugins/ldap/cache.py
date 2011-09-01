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
    record = recordProvider()
    servers = record.value.split()
    if servers:
        return Memcached(servers)
    return NullCache()