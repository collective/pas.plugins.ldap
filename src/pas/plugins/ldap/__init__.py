"""Init and utils."""

from . import monkey  # noqa
from .plugin import LDAPPlugin
from .plugin import manage_addLDAPPlugin
from .plugin import manage_addLDAPPluginForm
from .plugin import zmidir
from AccessControl.Permissions import add_user_folders
from Products.PluggableAuthService import registerMultiPlugin
from zope.i18nmessageid import MessageFactory

import logging
import os


PACKAGE_NAME = "pas.plugins.ldap"

_ = MessageFactory(PACKAGE_NAME)

logger = logging.getLogger(PACKAGE_NAME)


def initialize(context):
    registerMultiPlugin(LDAPPlugin.meta_type)
    context.registerClass(
        LDAPPlugin,
        permission=add_user_folders,
        icon=os.path.join(zmidir, "ldap.png"),
        constructors=(manage_addLDAPPluginForm, manage_addLDAPPlugin),
        visibility=None,
    )
