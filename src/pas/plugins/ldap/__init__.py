from AccessControl.Permissions import add_user_folders
from . import monkey  # noqa
from . import LDAPPlugin
from . import manage_addLDAPPlugin
from . import manage_addLDAPPluginForm
from . import zmidir
from Products.PluggableAuthService import registerMultiPlugin

import os


def initialize(context):
    registerMultiPlugin(LDAPPlugin.meta_type)
    context.registerClass(
        LDAPPlugin,
        permission=add_user_folders,
        icon=os.path.join(zmidir, "ldap.png"),
        constructors=(manage_addLDAPPluginForm, manage_addLDAPPlugin),
        visibility=None,
    )
