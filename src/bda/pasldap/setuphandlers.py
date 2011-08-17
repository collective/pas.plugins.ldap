from StringIO import StringIO
from bda.pasldap._plugin import LDAPPlugin


def isNotThisProfile(context):
    return context.readDataFile("bdapasldap_marker.txt") is None


def _addPlugin(pas):
    installed = pas.objectIds()
    ID = 'ldap_bda'
    TITLE = 'BDA LDAP plugin'
    if ID in installed:
        return TITLE + " already installed."
    plugin = LDAPPlugin(ID, title=TITLE)
    pas._setObject(ID, plugin)
    for info in pas.plugins.listPluginTypeInfo():
        interface = info['interface']
        if not interface.providedBy(plugin):
            continue
        pas.plugins.activatePlugin(interface, plugin.getId())
        pas.plugins.movePluginsDown(
            interface,
            [x[0] for x in pas.plugins.listPlugins(interface)[:-1]],
        )


def setupPlugin(context):
    if isNotThisProfile(context):
        return 
    site = context.getSite()
    pas = site.acl_users
    _addPlugin(pas)