from zope.interface import implementer
from zope.component import queryUtility
from bda.cache import (
    Memcached,
    NullCache,
)
from node.ext.ldap.interfaces import ICacheProviderFactory
from .interfaces import ICacheSettingsRecordProvider

@implementer(ICacheProviderFactory)
def cacheProviderFactory():
    recordProvider = queryUtility(ICacheSettingsRecordProvider)
    if not recordProvider:
        return NullCache()
    record = recordProvider()
    servers = record.value.split()
    if servers:
        return Memcached(servers)
    return NullCache()