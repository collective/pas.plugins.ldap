from plone.base.interfaces import INonInstallable
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles:
    """This hides zope2 profile from the quick installer tool and plone control panel"""

    _hidden = [
        "pas.plugins.ldap:default",
        "pas.plugins.ldap.plonecontrolpanel:install-base",
    ]

    def getNonInstallableProducts(self):
        """Hide the whole product from the quick installer tool."""
        return self._hidden

    def getNonInstallableProfiles(self):
        """Hide specific profiles from the quick installer tool and plone control panel."""
        return self._hidden
