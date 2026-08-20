"""Cache settings record provider for plone registry"""

from persistent import Persistent
from plone.registry import Record, field
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from zope.interface import implementer

from pas.plugins.ldap import _

from ..interfaces import ICacheSettingsRecordProvider

REGKEY = "pas.plugins.ldap.memcached"


class NullRecord:
    """A null record that returns an empty string for its value."""

    value = ""


@implementer(ICacheSettingsRecordProvider)
class CacheSettingsRecordProvider(Persistent):
    """Provides a registry record for LDAP cache settings."""

    def __call__(self):
        registry = queryUtility(IRegistry)
        if not registry:
            # XXX must not happen, be gentle anyway
            return NullRecord()
        records = registry.records
        if REGKEY not in records:
            # init if not exist
            value = field.TextLine(title=_("servers, delimited by space"))
            records[REGKEY] = Record(value)
        return records[REGKEY]
