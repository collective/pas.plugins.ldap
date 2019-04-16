# -*- coding: utf-8 -*-
from pas.plugins.ldap.plugin import LDAPPlugin
from zope.component.hooks import getSite


TITLE = "LDAP plugin (pas.plugins.ldap)"


def _addPlugin(pas, pluginid="pasldap"):
    installed = pas.objectIds()
    if pluginid in installed:
        return TITLE + " already installed."
    plugin = LDAPPlugin(pluginid, title=TITLE)
    pas._setObject(pluginid, plugin)
    plugin = pas[plugin.getId()]  # get plugin acquisition wrapped!
    for info in pas.plugins.listPluginTypeInfo():
        interface = info["interface"]
        if not interface.providedBy(plugin):
            continue
        pas.plugins.activatePlugin(interface, plugin.getId())
        pas.plugins.movePluginsDown(
            interface, [x[0] for x in pas.plugins.listPlugins(interface)[:-1]]
        )


def post_install(context):
    site = getSite()
    pas = site.acl_users
    _addPlugin(pas)
