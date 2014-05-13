# -*- coding: utf-8 -*-
from Products.CMFQuickInstallerTool.interfaces import INonInstallable
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles(object):
    """This hides zope2 profile from the quick installer tool.
    """

    def getNonInstallableProducts(self):
        return ['pas.plugins.ldap']
