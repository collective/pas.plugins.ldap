import os
from AccessControl.Permissions import add_user_folders
from Products.PluggableAuthService import registerMultiPlugin
from .plugin import (
    LDAPPlugin,
    manage_addLDAPPlugin,
    manage_addLDAPPluginForm,
    zmidir,
)


# XXX temp
import monkey


def initialize(context):
    registerMultiPlugin(LDAPPlugin.meta_type)
    context.registerClass(
        LDAPPlugin,
        permission=add_user_folders,
        icon=os.path.join(zmidir, "ldap.png"),
        constructors=(manage_addLDAPPluginForm, manage_addLDAPPlugin),
        visibility=None
    )
