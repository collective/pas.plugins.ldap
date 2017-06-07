# -*- coding: utf-8 -*-
from zope.interface import Interface


class ILDAPPlugin(Interface):
    """Marker Interface for the LDAP Plugin
    """


class ICacheSettingsRecordProvider(Interface):
    """cache settings provider, expects to return a record on call
    In future this may be used more generic.
    """


VALUE_NOT_CACHED = dict()


class IPluginCacheHandler(Interface):
    """Handles caching of the node trees used in the PAS Plugin
    """

    def get():
        """the cached value or VALUE_NOT_CACHED
        """

    def set(value):
        """sets a value in the cache
        """

    def invalidate():
        """removes a value from the cache
        """
