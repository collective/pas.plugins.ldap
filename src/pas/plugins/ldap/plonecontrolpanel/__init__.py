from zope.interface import implementer
from Products.CMFQuickInstallerTool.interfaces import INonInstallable


@implementer(INonInstallable)
class HiddenProfiles(object):
    """This hides zope2 profile from the quick installer tool.
    """

    def getNonInstallableProducts(self):
        return ['pas.plugins.ldap']
