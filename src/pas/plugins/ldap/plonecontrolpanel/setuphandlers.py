"""Setup handlers for the LDAP plugin."""

from pas.plugins.ldap import PACKAGE_NAME
from pas.plugins.ldap.plugin import LDAPPlugin
from zope.component.hooks import getSite

import contextlib
import logging


logger = logging.getLogger(PACKAGE_NAME)


TITLE = "LDAP plugin (pas.plugins.ldap)"


def _removePlugin(pas, PLUGIN_ID="pasldap"):
    """Remove the LDAP plugin from the given PAS instance."""
    # get the list of installed plugins
    installed = pas.objectIds()
    # check if plugin is installed
    if PLUGIN_ID not in installed:
        logger.info("LDAPPlugin '%s' is not installed in acl_users.", PLUGIN_ID)
        return TITLE + " already uninstalled."
    plugin = getattr(pas, PLUGIN_ID)
    if not isinstance(plugin, LDAPPlugin):
        logger.warning(
            "Uninstall aborted. PAS plugin %s is not an LDAPPlugin.", PLUGIN_ID
        )
    for info in pas.plugins.listPluginTypeInfo():
        interface = info["interface"]
        if not interface.providedBy(plugin):
            continue
        # the plugin may not be active
        with contextlib.suppress(KeyError):
            pas.plugins.deactivatePlugin(interface, plugin.getId())
    pas._delObject(PLUGIN_ID)
    logger.info("Removed LDAPPlugin %s from acl_users.", PLUGIN_ID)


def uninstall(context):
    """Uninstall pas.plugins.ldap."""
    site = getSite()
    pas = site.acl_users
    _removePlugin(pas)
