# Copyright (c) 2006-2009 BlueDynamics Alliance, Austria http://bluedynamics.com
# GNU General Public License (GPL)

from AccessControl.Permissions import add_user_folders
from Products.PluggableAuthService import registerMultiPlugin
from bda.pasldap._plugin import (
    LDAPPlugin,
    manage_addLDAPPluginForm,
    manage_addLDAPPlugin 
)

def initialize(context):
    registerMultiPlugin(LDAPPlugin.meta_type)
    context.registerClass(
        LDAPPlugin,
        permission=add_user_folders,
        icon="www/ldap.gif",
        constructors=(
            manage_addLDAPPluginForm,
            manage_addLDAPPlugin,
        ),
        visibility=None
    )
