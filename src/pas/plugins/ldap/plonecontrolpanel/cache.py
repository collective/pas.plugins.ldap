from ..interfaces import ICacheSettingsRecordProvider
from persistent import Persistent
from plone.registry import field
from plone.registry import Record
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from zope.interface import implementer


REGKEY = "pas.plugins.ldap.memcached"


class NullRecord:
    value = ""


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
            value = field.TextLine(title="servers, delimited by space")
            records[REGKEY] = Record(value)
        return records[REGKEY]
