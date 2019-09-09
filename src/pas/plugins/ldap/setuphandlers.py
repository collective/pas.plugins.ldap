# -*- coding: utf-8 -*-
from pas.plugins.ldap.plugin import LDAPPlugin
from zope.component.hooks import getSite


TITLE = "LDAP plugin (pas.plugins.ldap)"


def remove_persistent_import_step(context):
    """Remove broken persistent import step.

    profile/import_steps.xml defined an import step with id
    "pas.plugins.ldap.setup" which pointed to
    pas.plugins.ldap.setuphandlers.setupPlugin.
    This function no longer exists, and the import step is not needed,
    because a post_install handler is now used for this.
    But you get an error in the log whenever you import a profile:

      GenericSetup Step pas.plugins.ldap.setup has an invalid import handler

    So we remove the step.
    """
    registry = context.getImportStepRegistry()
    import_step = "pas.plugins.ldap.setup"
    if import_step in registry._registered:
        registry.unregisterStep(import_step)


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
