import yafowil.loader

from zope.interface import implements
from Products.CMFQuickInstallerTool.interfaces import INonInstallable

class HiddenProfiles(object):
    """This hides zope2 profile from the quick installer tool."""
    implements(INonInstallable)

    def getNonInstallableProducts(self):
        return ['pas.plugins.ldap']
