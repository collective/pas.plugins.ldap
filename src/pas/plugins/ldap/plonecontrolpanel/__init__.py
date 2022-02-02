from Products.CMFPlone.interfaces.installable import INonInstallable
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles:
    """This hides zope2 profile from the quick installer tool and plone cpanel"""

    _hidden = [
        "pas.plugins.ldap:default",
        "pas.plugins.ldap.plonecontrolpanel:install-base",
    ]

    def getNonInstallableProducts(self):
        return self._hidden

    def getNonInstallableProfiles(self):
        return self._hidden
