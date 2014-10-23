# -*- coding: utf-8 -*-
from AccessControl.Permissions import add_user_folders
from Products.PluggableAuthService import registerMultiPlugin
from pas.plugins.ldap.plugin import LDAPPlugin
from pas.plugins.ldap.plugin import manage_addLDAPPlugin
from pas.plugins.ldap.plugin import manage_addLDAPPluginForm
from pas.plugins.ldap.plugin import zmidir

import os
import monkey  # noqa


def initialize(context):
    registerMultiPlugin(LDAPPlugin.meta_type)
    context.registerClass(
        LDAPPlugin,
        permission=add_user_folders,
        icon=os.path.join(zmidir, 'ldap.png'),
        constructors=(manage_addLDAPPluginForm, manage_addLDAPPlugin),
        visibility=None
    )
