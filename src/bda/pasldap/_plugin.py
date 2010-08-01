# Copyright (c) 2006-2009 BlueDynamics Alliance, Austria http://bluedynamics.com
# GNU General Public License (GPL)

import logging
logger = logging.getLogger('LDAPPlugin')

from zope.component import getUtility
from zope.interface import Interface, implements
from Products.CMFPlone.interfaces import IPloneSiteRoot



#import socket, os
#import types
#from sets import Set

#from Acquisition import Implicit, aq_parent, aq_base, aq_inner
#from AccessControl import getSecurityManager
#from OFS.Cache import Cacheable
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
#from Products.PluggableAuthService.permissions import ManageGroups
#from Products.PluggableAuthService.UserPropertySheet import UserPropertySheet
from Products.PluggableAuthService.interfaces.plugins import (
    IUserEnumerationPlugin,
#    IGroupsPlugin,
#    IGroupEnumerationPlugin,
#    IRolesPlugin,
#    IPropertiesPlugin,
#    IRoleEnumerationPlugin,
)
from Products.PlonePAS.interfaces.group import IGroupIntrospection
from Products.PlonePAS.plugins.group import PloneGroup

def addLDAPPlugin(pas, id, title):
    """Factory method to instantiate an LDAPPlugin and add to pas.
    """
    # Instantiate the folderish adapter object
    plugin = LDAPPlugin(id, title=title)
    pas._setObject(id, plugin)

class ILDAPPlugin(Interface):
    """Marker Interface"""

class LDAPPlugin(BasePlugin):
    ''' fetches group info from LDAP and provides in PAS'''

    meta_type = 'LDAPPlugin'
    # so far the interfaces that also Products.LDAPMultiPlugins supports
    implements(ILDAPPlugin,
            IUserEnumerationPlugin,
#            IGroupsPlugin,
#            IGroupEnumerationPlugin,
#            IRoleEnumerationPlugin,
#            IAuthenticationPlugin,
#            ICredentialsResetPlugin,
#            IPropertiesPlugin,
#            IRolesPlugin,
            )

    def __init__(self, id, title=None):
        self.id = id
        self.title = title
        self._portal = getUtility(IPloneSiteRoot)

    @property
    def ldap(self):
        try:
            return self._v_ldap
        except AttributeError:
            self._v_ldap = self._init_ldap()
            return self._v_ldap

    def _init_ldap(self):
        # get config

        # create users / groups
        # return user / groups
        pass
