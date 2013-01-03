from zope.interface import Interface


class ILDAPPlugin(Interface):
    """Marker Interface for the LDAP Plugin
    """


class ICacheSettingsRecordProvider(Interface):
    """cache settings provider, expects to return a record on call
    In future this may be used more generic.
    """
