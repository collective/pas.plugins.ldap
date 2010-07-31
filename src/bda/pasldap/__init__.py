# Copyright (c) 2006-2009 BlueDynamics Alliance, Austria http://bluedynamics.com
# GNU General Public License (GPL)

from AccessControl.Permissions import add_user_folders
from Products.PluggableAuthService import registerMultiPlugin
from Products.PASGroupsFromLDAP._plugin import (
    GroupsFromLDAPMultiPlugin,
    manage_addGroupsFromLDAPMultiPluginForm,
    manage_addGroupsFromLDAPMultiPlugin 
)

def initialize(context):
    registerMultiPlugin(GroupsFromLDAPMultiPlugin.meta_type)
    context.registerClass(
        GroupsFromLDAPMultiPlugin,
        permission=add_user_folders,
        icon="www/ldap.gif",
        constructors=(
            manage_addGroupsFromLDAPMultiPluginForm,
            manage_addGroupsFromLDAPMultiPlugin,
        ),
        visibility=None
    )