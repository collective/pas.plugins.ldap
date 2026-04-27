# -*- coding: utf-8 -*-
from zope.component.hooks import getSite
from pas.plugins.ldap.plugin import LDAPPlugin
import logging


logger = logging.getLogger(__name__)


TITLE = "LDAP plugin (pas.plugins.ldap)"


def _removePlugin(pas, PLUGIN_ID="pasldap"):
    installed = pas.objectIds()
    if PLUGIN_ID not in installed:
        return TITLE + " already uninstalled."
    plugin = getattr(pas, PLUGIN_ID)
    if not isinstance(plugin, LDAPPlugin):
        logger.warning(
            "Uninstall aborted. PAS plugin %s is not an LDAPPlugin.",
             PLUGIN_ID)
    for info in pas.plugins.listPluginTypeInfo():
        interface = info["interface"]
        if not interface.providedBy(plugin):
            continue
        try:
            pas.plugins.deactivatePlugin(interface, plugin.getId())
        except KeyError:
            # the plugin was not active
            pass
    pas._delObject(PLUGIN_ID)
    logger.info("Removed LDAPPlugin %s from acl_users.", PLUGIN_ID)


def uninstall(context):
    site = getSite()
    pas = site.acl_users
    _removePlugin(pas)
    