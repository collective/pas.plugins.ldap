# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces.installable import INonInstallable
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles(object):
    """This hides zope2 profile from the quick installer tool and plone cpanel
    """

    _hidden = [
        u"pas.plugins.ldap:default",
        u"pas.plugins.ldap.plonecontrolpanel:install-base",
    ]

    def getNonInstallableProducts(self):
        return self._hidden

    def getNonInstallableProfiles(self):
        return self._hidden
