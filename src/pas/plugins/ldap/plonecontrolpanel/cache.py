from zope.interface import implementer
from zope.component import queryUtility
from persistent import Persistent
from plone.registry import (
    field,
    Record,
)
from plone.registry.interfaces import IRegistry
from pas.plugins.ldap.interfaces import ICacheSettingsRecordProvider


REGKEY = 'pas.plugins.ldap.memcached'


class NullRecord(object):
    value = ''


@implementer(ICacheSettingsRecordProvider)
class CacheSettingsRecordProvider(Persistent):

    def __call__(self):
        registry = queryUtility(IRegistry)
        if not registry:
            # XXX must not happen, be gentle anyway
            return NullRecord()
        records = registry.records
        if REGKEY not in records:
            # init if not exist
            value = field.TextLine(title=u'servers, delimited by space')
            records[REGKEY] = Record(value)
        return records[REGKEY]
